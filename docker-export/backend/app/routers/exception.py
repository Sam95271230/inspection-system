from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from typing import Optional, List

from app.database import get_db
from app.models.exception import ExceptionTicket, ExceptionHistory
from app.models.inspection import Inspection
from app.models.user import SysUser
from app.models.plant_dict import Plant
from app.utils.response import success
from app.dependencies import get_current_user
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

    return success({
        "id": str(ticket.id),
        "inspection_id": str(ticket.inspection_id),
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

    return success(data)


@router.post("/{ticket_id}/assign")
async def assign_exception(
    ticket_id: str,
    req: AssignRequest,
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

    return success({"id": str(ticket.id), "status": ticket.status})


@router.post("/{ticket_id}/process")
async def process_exception(
    ticket_id: str,
    req: ProcessRequest,
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

    return success({"id": str(ticket.id), "status": ticket.status})


@router.post("/{ticket_id}/approve")
async def approve_exception(
    ticket_id: str,
    req: ApproveRequest,
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

    return success({"id": str(ticket.id), "status": ticket.status})


@router.post("/{ticket_id}/reject")
async def reject_exception(
    ticket_id: str,
    req: RejectRequest,
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

    return success({"id": str(ticket.id), "status": ticket.status})


@router.post("/{ticket_id}/reprocess")
async def reprocess_exception(
    ticket_id: str,
    req: ReprocessRequest,
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

    return success({"id": str(ticket.id), "status": ticket.status})
