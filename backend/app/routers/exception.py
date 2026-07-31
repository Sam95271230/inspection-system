from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from typing import Optional, List
import os

from app.database import get_db
from app.models.exception import ExceptionTicket, ExceptionHistory
from app.models.inspection import Inspection, InspectionImage
from app.models.user import SysUser
from app.models.plant_dict import Plant
from app.utils.response import success
from app.dependencies import get_current_user
from app.utils.minio_client import get_minio_client
from pydantic import BaseModel

router = APIRouter(prefix="/exceptions", tags=["异常签核"])


class ExceptionStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PENDING_SIGNOFF = "PENDING_SIGNOFF"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class AssignRequest(BaseModel):
    remark: Optional[str] = None
    assignee_id: str


class ProcessRequest(BaseModel):
    remark: Optional[str] = None
    attachment_urls: Optional[List[str]] = None


class ApproveRequest(BaseModel):
    remark: Optional[str] = None


class RejectRequest(BaseModel):
    remark: Optional[str] = None


class ReprocessRequest(BaseModel):
    remark: Optional[str] = None


async def add_history(db, ticket_id, from_status, to_status, operator_id, action, remark, attachment_urls):
    history = ExceptionHistory(
        ticket_id=ticket_id,
        from_status=from_status,
        to_status=to_status,
        operator_id=operator_id,
        action=action,
        remark=remark,
        attachment_urls=attachment_urls or [],
    )
    db.add(history)
    await db.flush()


async def _get_inspection_images(db, inspection_id) -> list:
    """获取巡检记录关联的图片 URL 列表"""
    result = await db.execute(
        select(InspectionImage).where(InspectionImage.inspection_id == inspection_id)
    )
    images = result.scalars().all()
    if not images:
        return []

    minio_client = get_minio_client()
    bucket = os.getenv("MINIO_BUCKET", "inspection-images")
    external_url = os.getenv("MINIO_EXTERNAL_URL", "http://localhost:9000")

    image_urls = []
    for img in images:
        url = f"{external_url}/{bucket}/{img.storage_key}"
        image_urls.append({
            "id": str(img.id),
            "file_name": img.file_name,
            "url": url,
            "sort_order": img.sort_order,
        })

    return image_urls


async def _send_mail_notification(to_email: str, subject: str, body: str):
    """发送邮件通知（后台任务），无邮件配置时静默跳过"""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_host, smtp_user, smtp_password]):
        return

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html", "utf-8"))

        with smtplib.SMTP(smtp_host, int(smtp_port), timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [to_email], msg.as_string())
        print(f"[邮件] 已发送至 {to_email}: {subject}")
    except Exception as e:
        print(f"[邮件] 发送失败: {e}")


async def _get_ticket_info(db, ticket: ExceptionTicket) -> dict:
    """获取异常单的完整上下文信息"""
    insp_result = await db.execute(
        select(Inspection).where(Inspection.id == ticket.inspection_id)
    )
    insp = insp_result.scalar_one_or_none()

    plant_result = await db.execute(
        select(Plant).where(Plant.id == ticket.plant_id)
    )
    plant = plant_result.scalar_one_or_none()

    return {
        "serial_no": insp.serial_no if insp else "N/A",
        "ip_address": insp.ip_address if insp else "N/A",
        "plant_name": plant.name if plant else "N/A",
        "title": ticket.title,
    }


async def _notify_exception_updated(db, ticket, action_name, operator):
    """根据状态变更发送邮件通知相关用户"""
    info = await _get_ticket_info(db, ticket)

    # 排除当前操作者之外，根据需要通知相关人
    notify_users = []

    if ticket.status == ExceptionStatus.PROCESSING and ticket.current_assignee_id:
        # 分配给处理人时通知处理人
        result = await db.execute(
            select(SysUser).where(SysUser.id == ticket.current_assignee_id)
        )
        assignee = result.scalar_one_or_none()
        if assignee and assignee.email and str(assignee.id) != str(operator.id):
            notify_users.append(assignee)
    elif ticket.status == ExceptionStatus.PENDING_SIGNOFF:
        # 提交处理结果后通知所有管理员
        result = await db.execute(
            select(SysUser).where(SysUser.is_superadmin.is_(True), SysUser.email.isnot(None))
        )
        admins = result.scalars().all()
        for admin in admins:
            if str(admin.id) != str(operator.id):
                notify_users.append(admin)
    elif ticket.status in (ExceptionStatus.CLOSED, ExceptionStatus.REJECTED):
        # 签核/驳回后通知最初提交人
        result = await db.execute(
            select(ExceptionHistory)
            .where(ExceptionHistory.ticket_id == ticket.id)
            .order_by(ExceptionHistory.created_at)
            .limit(1)
        )
        first_history = result.scalar_one_or_none()
        if first_history:
            submitter_result = await db.execute(
                select(SysUser).where(SysUser.id == first_history.operator_id, SysUser.email.isnot(None))
            )
            submitter = submitter_result.scalar_one_or_none()
            if submitter and str(submitter.id) != str(operator.id):
                notify_users.append(submitter)

    # 发送邮件
    for user in notify_users:
        subject = f"[巡检系统] 异常单 {info['serial_no']} - {action_name}"
        body = f"""
        <h3>异常单状态更新</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse">
          <tr><td><b>巡检单号</b></td><td>{info['serial_no']}</td></tr>
          <tr><td><b>IP 地址</b></td><td>{info['ip_address']}</td></tr>
          <tr><td><b>厂区</b></td><td>{info['plant_name']}</td></tr>
          <tr><td><b>异常摘要</b></td><td>{info['title']}</td></tr>
          <tr><td><b>当前状态</b></td><td>{ticket.status}</td></tr>
          <tr><td><b>操作人</b></td><td>{operator.real_name or operator.username}</td></tr>
        </table>
        <p>请登录巡检系统查看详情。</p>
        """
        await _send_mail_notification(user.email, subject, body)


@router.get("")
async def list_exceptions(
    status: str = None,
    plant_id: str = None,
    page: int = 1,
    page_size: int = 10,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_superadmin:
        from app.dependencies import get_authorized_plant_ids
        authorized_plants = await get_authorized_plant_ids(current_user, db)
        if not authorized_plants:
            return success({"list": [], "total": 0})

    stmt = select(ExceptionTicket).order_by(desc(ExceptionTicket.created_at))

    if not current_user.is_superadmin:
        stmt = stmt.where(ExceptionTicket.plant_id.in_(authorized_plants))

    if status:
        stmt = stmt.where(ExceptionTicket.status == status)
    if plant_id:
        stmt = stmt.where(ExceptionTicket.plant_id == plant_id)

    offset = (page - 1) * page_size
    result = await db.execute(stmt.offset(offset).limit(page_size))
    tickets = result.scalars().all()

    count_result = await db.execute(select(ExceptionTicket))
    total = len(count_result.scalars().all())

    inspection_ids = [t.inspection_id for t in tickets]
    inspections = {}
    if inspection_ids:
        insp_result = await db.execute(select(Inspection).where(Inspection.id.in_(inspection_ids)))
        for insp in insp_result.scalars().all():
            inspections[str(insp.id)] = insp

    plant_ids = [t.plant_id for t in tickets]
    plants = {}
    if plant_ids:
        plant_result = await db.execute(select(Plant).where(Plant.id.in_(plant_ids)))
        for p in plant_result.scalars().all():
            plants[str(p.id)] = p

    assignee_ids = [t.current_assignee_id for t in tickets if t.current_assignee_id]
    assignees = {}
    if assignee_ids:
        user_result = await db.execute(select(SysUser).where(SysUser.id.in_(assignee_ids)))
        for u in user_result.scalars().all():
            assignees[str(u.id)] = u

    data = []
    for t in tickets:
        insp = inspections.get(str(t.inspection_id), None)
        plant = plants.get(str(t.plant_id), None)
        assignee = assignees.get(str(t.current_assignee_id), None) if t.current_assignee_id else None
        data.append({
            "id": str(t.id),
            "inspection_id": str(t.inspection_id),
            "serial_no": insp.serial_no if insp else None,
            "ip_address": insp.ip_address if insp else None,
            "plant_id": str(t.plant_id),
            "plant_name": plant.name if plant else None,
            "title": t.title,
            "status": t.status,
            "current_assignee_id": str(t.current_assignee_id) if t.current_assignee_id else None,
            "current_assignee_name": (assignee.real_name or assignee.username) if assignee else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return success({"list": data, "total": total})


@router.get("/{ticket_id}")
async def get_exception(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ExceptionTicket).where(ExceptionTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="异常单不存在")

    insp_result = await db.execute(select(Inspection).where(Inspection.id == ticket.inspection_id))
    insp = insp_result.scalar_one_or_none()

    return success({
        "id": str(ticket.id),
        "inspection_id": str(ticket.inspection_id),
        "serial_no": insp.serial_no if insp else None,
        "ip_address": insp.ip_address if insp else None,
        "plant_id": str(ticket.plant_id),
        "title": ticket.title,
        "status": ticket.status,
        "current_assignee_id": str(ticket.current_assignee_id) if ticket.current_assignee_id else None,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
    })


@router.get("/{ticket_id}/history")
async def get_exception_history(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ExceptionTicket).where(ExceptionTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="异常单不存在")

    # 获取巡检图片（与异常单关联的原始巡检记录图片）
    inspection_images = await _get_inspection_images(db, ticket.inspection_id)

    # 获取历史记录
    result = await db.execute(
        select(ExceptionHistory)
        .where(ExceptionHistory.ticket_id == ticket_id)
        .order_by(desc(ExceptionHistory.created_at))
    )
    histories = result.scalars().all()

    operator_ids = [h.operator_id for h in histories]
    operators = {}
    if operator_ids:
        user_result = await db.execute(select(SysUser).where(SysUser.id.in_(operator_ids)))
        for u in user_result.scalars().all():
            operators[str(u.id)] = u

    data = []
    for h in histories:
        op = operators.get(str(h.operator_id), None)
        data.append({
            "id": str(h.id),
            "from_status": h.from_status,
            "to_status": h.to_status,
            "operator_id": str(h.operator_id),
            "operator_name": (op.real_name or op.username) if op else None,
            "action": h.action,
            "remark": h.remark,
            "attachment_urls": h.attachment_urls or [],
            "created_at": h.created_at.isoformat() if h.created_at else None,
        })

    return success({
        "history": data,
        "images": inspection_images,
        "inspection_id": str(ticket.inspection_id),
        "serial_no": ticket.title,
    })


@router.post("/{ticket_id}/assign")
async def assign_exception(
    ticket_id: str,
    req: AssignRequest,
    background_tasks: BackgroundTasks,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ExceptionTicket).where(ExceptionTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="异常单不存在")

    if ticket.status != ExceptionStatus.PENDING:
        raise HTTPException(status_code=400, detail="当前状态不允许分配")

    if not req.assignee_id:
        raise HTTPException(status_code=400, detail="请选择处理人")

    from_status = ticket.status
    ticket.status = ExceptionStatus.PROCESSING
    ticket.current_assignee_id = req.assignee_id

    await add_history(
        db, ticket.id, from_status, ticket.status,
        current_user.id, "ASSIGN", req.remark, []
    )
    await db.commit()
    await db.refresh(ticket)

    # 邮件通知处理人
    background_tasks.add_task(_notify_exception_updated, db, ticket, "已分配处理人", current_user)

    return success({"id": str(ticket.id), "status": ticket.status})


@router.post("/{ticket_id}/process")
async def process_exception(
    ticket_id: str,
    req: ProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ExceptionTicket).where(ExceptionTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="异常单不存在")

    if ticket.status != ExceptionStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="当前状态不允许提交处理结果")

    if str(ticket.current_assignee_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="只有当前处理人可以提交处理结果")

    from_status = ticket.status
    ticket.status = ExceptionStatus.PENDING_SIGNOFF

    await add_history(
        db, ticket.id, from_status, ticket.status,
        current_user.id, "PROCESS", req.remark, req.attachment_urls
    )
    await db.commit()
    await db.refresh(ticket)

    # 邮件通知管理员签核
    background_tasks.add_task(_notify_exception_updated, db, ticket, "待签核", current_user)

    return success({"id": str(ticket.id), "status": ticket.status})


@router.post("/{ticket_id}/approve")
async def approve_exception(
    ticket_id: str,
    req: ApproveRequest,
    background_tasks: BackgroundTasks,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ExceptionTicket).where(ExceptionTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="异常单不存在")

    if ticket.status != ExceptionStatus.PENDING_SIGNOFF:
        raise HTTPException(status_code=400, detail="当前状态不允许签核")

    from_status = ticket.status
    ticket.status = ExceptionStatus.CLOSED

    await add_history(
        db, ticket.id, from_status, ticket.status,
        current_user.id, "APPROVE", req.remark, []
    )
    await db.commit()
    await db.refresh(ticket)

    # 邮件通知提交人已签核通过
    background_tasks.add_task(_notify_exception_updated, db, ticket, "签核通过", current_user)

    return success({"id": str(ticket.id), "status": ticket.status})


@router.post("/{ticket_id}/reject")
async def reject_exception(
    ticket_id: str,
    req: RejectRequest,
    background_tasks: BackgroundTasks,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ExceptionTicket).where(ExceptionTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="异常单不存在")

    if ticket.status != ExceptionStatus.PENDING_SIGNOFF:
        raise HTTPException(status_code=400, detail="当前状态不允许驳回")

    from_status = ticket.status
    ticket.status = ExceptionStatus.REJECTED

    await add_history(
        db, ticket.id, from_status, ticket.status,
        current_user.id, "REJECT", req.remark, []
    )
    await db.commit()
    await db.refresh(ticket)

    # 邮件通知提交人已驳回
    background_tasks.add_task(_notify_exception_updated, db, ticket, "签核驳回", current_user)

    return success({"id": str(ticket.id), "status": ticket.status})


@router.post("/{ticket_id}/reprocess")
async def reprocess_exception(
    ticket_id: str,
    req: ReprocessRequest,
    background_tasks: BackgroundTasks,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ExceptionTicket).where(ExceptionTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="异常单不存在")

    if ticket.status != ExceptionStatus.REJECTED:
        raise HTTPException(status_code=400, detail="当前状态不允许重新处理")

    from_status = ticket.status
    ticket.status = ExceptionStatus.PROCESSING

    await add_history(
        db, ticket.id, from_status, ticket.status,
        current_user.id, "REPROCESS", req.remark, []
    )
    await db.commit()
    await db.refresh(ticket)

    # 邮件通知处理人需重新处理
    background_tasks.add_task(_notify_exception_updated, db, ticket, "重新处理", current_user)

    return success({"id": str(ticket.id), "status": ticket.status})