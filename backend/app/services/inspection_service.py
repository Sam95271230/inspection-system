"""
巡检业务共享服务层
"""
import uuid as uuid_module
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.inspection import Inspection, InspectionImage
from app.models.exception import ExceptionTicket
from app.models.user import SysUser, user_plant
from app.constants import STATUS_LABEL_MAP


async def create_exception_for_inspection(
    db: AsyncSession,
    inspection: Inspection,
    antivirus_status: str,
    domain_status: str,
    plant_id,
    operator_id,
    serial_no: str,
) -> ExceptionTicket | None:
    """
    根据巡检状态判断是否需要创建异常工单，并自动分配给厂区 MEMBER。
    返回创建的 ExceptionTicket，或 None（无需创建）。
    """
    is_normal = (
        antivirus_status == "NORMAL"
        and domain_status in ("JOINED", "NOT_APPLICABLE")
    )
    if is_normal:
        return None

    title_parts = []
    if antivirus_status != "NORMAL":
        label = STATUS_LABEL_MAP.get(antivirus_status, antivirus_status)
        title_parts.append(f"防毒软件{label}")
    if domain_status not in ("JOINED", "NOT_APPLICABLE"):
        label = STATUS_LABEL_MAP.get(domain_status, domain_status)
        title_parts.append(label)
    title = " - ".join(title_parts) if title_parts else "巡检异常"

    # 自动分配给厂区 MEMBER
    member_result = await db.execute(
        select(SysUser)
        .join(user_plant, (user_plant.c.user_id == SysUser.id) & (user_plant.c.plant_id == plant_id) & (user_plant.c.role == "MEMBER"))
        .where(SysUser.is_active.is_(True))
        .limit(1)
    )
    assignee = member_result.scalar_one_or_none()

    exception_ticket = ExceptionTicket(
        inspection_id=inspection.id,
        plant_id=plant_id,
        title=title,
        status="PROCESSING" if assignee else "PENDING",
        current_assignee_id=assignee.id if assignee else None,
    )
    db.add(exception_ticket)
    await db.flush()

    # 记录创建和分配历史
    from app.routers.exception import add_history
    await add_history(
        db, exception_ticket.id, None,
        "PROCESSING" if assignee else "PENDING",
        operator_id, "CREATE",
        f"巡检 {serial_no} 触发异常", []
    )
    if assignee:
        await add_history(
            db, exception_ticket.id, "PROCESSING", "PROCESSING",
            operator_id, "AUTO_ASSIGN",
            f"自动分配给厂区Member: {assignee.real_name or assignee.username}", []
        )

    return exception_ticket, assignee


def build_inspection_query(
    stmt,
    plant_id: str = None,
    line_id: str = None,
    station_id: str = None,
    start_time: str = None,
    end_time: str = None,
    antivirus_status: str = None,
    domain_status: str = None,
):
    """构建巡检记录查询的通用筛选条件"""
    if plant_id:
        stmt = stmt.where(Inspection.plant_id == plant_id)
    if line_id:
        stmt = stmt.where(Inspection.line_id == line_id)
    if station_id:
        stmt = stmt.where(Inspection.station_id == station_id)
    if antivirus_status:
        stmt = stmt.where(Inspection.antivirus_status == antivirus_status)
    if domain_status:
        stmt = stmt.where(Inspection.domain_status == domain_status)
    if start_time:
        stmt = stmt.where(Inspection.inspect_time >= start_time)
    if end_time:
        stmt = stmt.where(Inspection.inspect_time <= end_time)
    return stmt


def parse_inspect_time(inspect_time_str: str | None) -> datetime:
    """解析巡检时间字符串，返回 native datetime"""
    if not inspect_time_str:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    try:
        t = datetime.fromisoformat(inspect_time_str.replace('Z', '+00:00'))
        return t.replace(tzinfo=None)
    except Exception:
        pass
    try:
        return datetime.strptime(inspect_time_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.now(timezone.utc).replace(tzinfo=None)
