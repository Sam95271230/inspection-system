from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from typing import Optional, List
import os
import json

from app.database import get_db
from app.models.exception import ExceptionTicket, ExceptionHistory
from app.models.inspection import Inspection, InspectionImage
from app.models.user import SysUser, user_plant
from app.models.plant_dict import Plant
from app.utils.response import success
from app.dependencies import get_current_user
from app.utils.minio_client import get_minio_client, upload_file, get_image_url, get_email_image_url
from app.routers.email_config import get_active_email_config, _send_email as send_mail
from app.constants import ExceptionStatus
from app.utils.email_templates import build_exception_email_body
from pydantic import BaseModel

router = APIRouter(prefix="/exceptions", tags=["异常签核"])


class AssignRequest(BaseModel):
    remark: Optional[str] = None
    assignee_id: str


class ProcessRequest(BaseModel):
    remark: Optional[str] = None
    attachment_urls: Optional[List[str]] = None
    images: Optional[List[dict]] = None  # 处理后图片：[{storage_key, name, url}]


class ApproveRequest(BaseModel):
    remark: Optional[str] = None


class RejectRequest(BaseModel):
    remark: Optional[str] = None


class ReprocessRequest(BaseModel):
    remark: Optional[str] = None
    images: Optional[List[dict]] = None


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

    image_urls = []
    for img in images:
        image_urls.append({
            "id": str(img.id),
            "file_name": img.file_name,
            "url": get_image_url(img.storage_key),
            "sort_order": img.sort_order,
        })

    return image_urls


async def _send_mail_notification(db, to_email: str, subject: str, body: str):
    """发送邮件通知（后台任务），无邮件配置时静默跳过"""
    config = await get_active_email_config(db)
    if not config:
        return

    try:
        send_mail(config, to_email, subject, body)
        print(f"[邮件] 已发送至 {to_email}: {subject}")
    except Exception as e:
        print(f"[邮件] 发送失败: {e}")


async def _build_email_body(db, ticket: ExceptionTicket, action_name: str, operator) -> str:
    """构建邮件正文，包含签核链接和巡检图片"""
    insp_result = await db.execute(
        select(Inspection).where(Inspection.id == ticket.inspection_id)
    )
    insp = insp_result.scalar_one_or_none()

    plant_result = await db.execute(
        select(Plant).where(Plant.id == ticket.plant_id)
    )
    plant = plant_result.scalar_one_or_none()

    # 获取巡检图片
    images = await _get_inspection_images(db, ticket.inspection_id)

    serial_no = insp.serial_no if insp else "N/A"
    ip = insp.ip_address if insp else "N/A"
    plant_name = plant.name if plant else "N/A"

    system_url = os.getenv("SYSTEM_URL", "http://localhost:8081")
    ticket_url = f"{system_url}/exceptions"
    operator_name = operator.real_name or operator.username

    # 状态中文映射
    status_map = {
        "PENDING": "待分配", "PROCESSING": "处理中",
        "PENDING_SIGNOFF": "待签核", "CLOSED": "已结案", "REJECTED": "已驳回"
    }

    # 图片HTML
    imgs_html = "<p><b>巡检证据图片：</b></p><div style='display:flex;flex-wrap:wrap;gap:8px;'>"
    if images:
        for img in images:
            imgs_html += f'<img src="{img["url"]}" style="width:200px;border:1px solid #ddd;border-radius:4px;" alt="{img["file_name"]}"/>'
    else:
        imgs_html += "<span style='color:#999;'>暂无图片</span>"
    imgs_html += "</div>"

    body = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 640px;">
    <h3 style="color: #409EFF;">巡检系统 - 异常单状态更新</h3>
    <table border="1" cellpadding="10" cellspacing="0" style="border-collapse:collapse; width:100%; border-color:#e4e7ed;">
      <tr><td style="background:#f5f7fa; width:120px;"><b>巡检单号</b></td><td>{serial_no}</td></tr>
      <tr><td style="background:#f5f7fa;"><b>IP 地址</b></td><td>{ip}</td></tr>
      <tr><td style="background:#f5f7fa;"><b>厂区</b></td><td>{plant_name}</td></tr>
      <tr><td style="background:#f5f7fa;"><b>异常摘要</b></td><td style="color:#e6a23c;font-weight:600;">{ticket.title}</td></tr>
      <tr><td style="background:#f5f7fa;"><b>当前状态</b></td><td>{status_map.get(ticket.status, ticket.status)}</td></tr>
      <tr><td style="background:#f5f7fa;"><b>操作人</b></td><td>{operator_name}</td></tr>
    </table>
    {imgs_html}
    <div style="margin-top:20px; padding:16px; background:#ecf5ff; border-radius:6px;">
      <p style="margin:0; font-size:14px;">
        <a href="{ticket_url}" style="color:#409EFF; font-weight:bold; text-decoration:none;">
          点击查看工单详情 &raquo;
        </a>
      </p>
      <p style="margin:8px 0 0 0; color:#909399; font-size:12px;">或复制链接：{ticket_url}</p>
    </div>
    <p style="margin-top:20px; color:#909399; font-size:12px;">此邮件由产线电脑巡检系统自动发送，请勿回复。</p>
    </body></html>
    """
    return body


async def _notify_exception_updated(ticket_id: str, action_name: str, operator_id: str):
    """根据状态变更发送邮件通知相关用户（创建独立 DB 会话）"""
    async for db in get_db():
        try:
            # 重新加载 ticket
            ticket_result = await db.execute(
                select(ExceptionTicket).where(ExceptionTicket.id == ticket_id)
            )
            ticket = ticket_result.scalar_one_or_none()
            if not ticket:
                return

            operator_result = await db.execute(
                select(SysUser).where(SysUser.id == operator_id)
            )
            operator = operator_result.scalar_one_or_none()
            if not operator:
                return

            notify_users = []

            if ticket.status == ExceptionStatus.PROCESSING and ticket.current_assignee_id:
                result = await db.execute(
                    select(SysUser).where(SysUser.id == ticket.current_assignee_id)
                )
                assignee = result.scalar_one_or_none()
                if assignee and assignee.email and str(assignee.id) != str(operator.id):
                    notify_users.append(assignee)
            elif ticket.status == ExceptionStatus.PENDING_SIGNOFF:
                result = await db.execute(
                    select(SysUser)
                    .join(user_plant, (user_plant.c.user_id == SysUser.id) & (user_plant.c.plant_id == ticket.plant_id) & (user_plant.c.role == "LEADER"))
                    .where(SysUser.is_active.is_(True), SysUser.email.isnot(None))
                )
                leaders = result.scalars().all()
                for leader in leaders:
                    if str(leader.id) != str(operator.id):
                        notify_users.append(leader)
                admin_result = await db.execute(
                    select(SysUser).where(SysUser.is_superadmin.is_(True), SysUser.email.isnot(None))
                )
                admins = admin_result.scalars().all()
                for admin in admins:
                    if str(admin.id) != str(operator.id) and admin not in leaders:
                        notify_users.append(admin)
            elif ticket.status in (ExceptionStatus.CLOSED, ExceptionStatus.REJECTED):
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

            for user in notify_users:
                insp_result = await db.execute(
                    select(Inspection).where(Inspection.id == ticket.inspection_id)
                )
                insp = insp_result.scalar_one_or_none()
                serial_no = insp.serial_no if insp else "N/A"
                subject = f"[巡检系统] 异常单 {serial_no} - {action_name}"
                body = await _build_email_body(db, ticket, action_name, operator)
                await _send_mail_notification(db, user.email, subject, body)
        finally:
            break  # get_db() only yields once


@router.post("/upload-image")
async def upload_exception_image(file: UploadFile = File(...)):
    """上传异常处理图片到 MinIO"""
    content = await file.read()
    object_name = f"exception/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    upload_file(object_name, content, file.content_type or "image/jpeg")
    return success({
        "url": get_image_url(object_name),
        "storage_key": object_name,
        "name": file.filename,
        "mime_type": file.content_type or "image/jpeg"
    })


@router.get("")
async def list_exceptions(
    status: str = None,
    plant_id: str = None,
    page: int = 1,
    page_size: int = 10,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    authorized_plants = []
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

    # 构建总数查询（应用相同过滤条件）
    from sqlalchemy import func as sql_func
    count_stmt = select(sql_func.count()).select_from(ExceptionTicket)
    if not current_user.is_superadmin:
        count_stmt = count_stmt.where(ExceptionTicket.plant_id.in_(authorized_plants))
    if status:
        count_stmt = count_stmt.where(ExceptionTicket.status == status)
    if plant_id:
        count_stmt = count_stmt.where(ExceptionTicket.plant_id == plant_id)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

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

    # 权限检查：只有超级管理员或厂区 Leader 可以手动分配
    if not await _check_is_plant_leader(db, current_user, ticket.plant_id):
        raise HTTPException(status_code=403, detail="只有该厂区的 Leader 或超级管理员可以分配工单")

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
    background_tasks.add_task(_notify_exception_updated, str(ticket.id), "已分配处理人", str(current_user.id))

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

    # 合并 attachment_urls 和 images 到历史记录
    all_attachments = list(req.attachment_urls or [])
    for img in (req.images or []):
        all_attachments.append(json.dumps(img, ensure_ascii=False))

    await add_history(
        db, ticket.id, from_status, ticket.status,
        current_user.id, "PROCESS", req.remark, all_attachments
    )

    # 自动分配给该厂区的 LEADER 签核
    leader_result = await db.execute(
        select(SysUser)
        .join(user_plant, (user_plant.c.user_id == SysUser.id) & (user_plant.c.plant_id == ticket.plant_id) & (user_plant.c.role == "LEADER"))
        .where(SysUser.is_active.is_(True))
        .limit(1)
    )
    leader = leader_result.scalar_one_or_none()
    if leader:
        ticket.current_assignee_id = leader.id
        await add_history(
            db, ticket.id, ticket.status, ticket.status,
            current_user.id, "AUTO_ASSIGN", f"自动转签核给厂区Leader: {leader.real_name or leader.username}", []
        )

    await db.commit()
    await db.refresh(ticket)

    # 邮件通知签核人（LEADER）
    background_tasks.add_task(_notify_exception_updated, str(ticket.id), "待签核", str(current_user.id))

    return success({"id": str(ticket.id), "status": ticket.status})


async def _check_is_plant_leader(db, user: SysUser, plant_id) -> bool:
    """检查用户是否为指定厂区的 Leader 或超级管理员"""
    if user.is_superadmin:
        return True
    result = await db.execute(
        select(user_plant.c.role).where(
            (user_plant.c.user_id == user.id) & (user_plant.c.plant_id == plant_id) & (user_plant.c.role == "LEADER")
        )
    )
    return result.scalar_one_or_none() is not None


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

    # 权限检查：只有厂区 Leader 或超级管理员可以签核
    if not await _check_is_plant_leader(db, current_user, ticket.plant_id):
        raise HTTPException(status_code=403, detail="只有该厂区的 Leader 或超级管理员可以签核")

    from_status = ticket.status
    ticket.status = ExceptionStatus.CLOSED

    await add_history(
        db, ticket.id, from_status, ticket.status,
        current_user.id, "APPROVE", req.remark, []
    )
    await db.commit()
    await db.refresh(ticket)

    # 邮件通知提交人已签核通过
    background_tasks.add_task(_notify_exception_updated, str(ticket.id), "签核通过", str(current_user.id))

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

    # 权限检查：只有厂区 Leader 或超级管理员可以驳回
    if not await _check_is_plant_leader(db, current_user, ticket.plant_id):
        raise HTTPException(status_code=403, detail="只有该厂区的 Leader 或超级管理员可以驳回")

    from_status = ticket.status
    ticket.status = ExceptionStatus.REJECTED

    await add_history(
        db, ticket.id, from_status, ticket.status,
        current_user.id, "REJECT", req.remark, []
    )
    await db.commit()
    await db.refresh(ticket)

    # 邮件通知提交人已驳回
    background_tasks.add_task(_notify_exception_updated, str(ticket.id), "签核驳回", str(current_user.id))

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

    # 合并图片到附件
    all_attachments = []
    for img in (req.images or []):
        all_attachments.append(json.dumps(img, ensure_ascii=False))

    await add_history(
        db, ticket.id, from_status, ticket.status,
        current_user.id, "REPROCESS", req.remark, all_attachments
    )
    await db.commit()
    await db.refresh(ticket)

    # 邮件通知处理人需重新处理
    background_tasks.add_task(_notify_exception_updated, str(ticket.id), "重新处理", str(current_user.id))

    return success({"id": str(ticket.id), "status": ticket.status})