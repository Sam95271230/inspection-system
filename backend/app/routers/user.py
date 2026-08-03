from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List

from app.database import get_db
from app.models.user import SysUser, Role, user_role, user_plant
from app.models.inspection import Inspection
from app.models.exception import ExceptionTicket
from app.security.password import get_password_hash
from app.utils.response import success
from app.schemas.user import UserCreate, UserUpdate
from app.dependencies import get_current_user, require_superadmin

router = APIRouter(prefix="/users", tags=["用户管理"])


async def _get_user_roles(db, user_id: str) -> list:
    """获取用户的角色信息（role_ids + role_names）"""
    result = await db.execute(
        select(user_role.c.role_id).where(user_role.c.user_id == user_id)
    )
    role_ids = [str(r[0]) for r in result.all()]
    role_names = []
    if role_ids:
        role_result = await db.execute(
            select(Role).where(Role.id.in_([r[0] for r in result.all()]))
        )
        role_names = [r.name for r in role_result.scalars().all()]
    return role_ids, role_names


async def _get_user_plants(db, user_id: str) -> list:
    """获取用户的厂区-角色映射 [{plant_id, role}]"""
    result = await db.execute(
        select(user_plant.c.plant_id, user_plant.c.role).where(user_plant.c.user_id == user_id)
    )
    return [{"plant_id": str(p[0]), "role": p[1] or "MEMBER"} for p in result.all()]


async def _build_user_response(db, user: SysUser) -> dict:
    role_ids, role_names = await _get_user_roles(db, user.id)
    plant_roles = await _get_user_plants(db, user.id)
    plant_ids = [p["plant_id"] for p in plant_roles]
    return {
        "id": str(user.id),
        "username": user.username,
        "real_name": user.real_name,
        "email": user.email,
        "mobile": user.mobile,
        "is_active": user.is_active,
        "is_superadmin": user.is_superadmin,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "role_ids": role_ids,
        "role_names": role_names,
        "plant_ids": plant_ids,
        "plant_roles": plant_roles,
    }


@router.post("")
async def create_user(
    data: UserCreate,
    current_user: SysUser = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SysUser).where(SysUser.username == data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = SysUser(
        username=data.username,
        password_hash=get_password_hash(data.password),
        real_name=data.real_name,
        email=data.email,
        mobile=data.mobile,
        is_active=data.is_active,
        is_superadmin=data.is_superadmin,
    )
    db.add(user)
    await db.flush()

    if data.role_ids:
        for role_id in data.role_ids:
            await db.execute(
                user_role.insert().values(user_id=user.id, role_id=role_id)
            )

    plant_roles = data.plant_roles or []
    # 向后兼容 plant_ids
    if not plant_roles and data.plant_ids:
        plant_roles = [{"plant_id": pid, "role": "MEMBER"} for pid in data.plant_ids]

    if plant_roles and not data.is_superadmin:
        for pr in plant_roles:
            await db.execute(
                user_plant.insert().values(
                    user_id=user.id,
                    plant_id=pr.plant_id if hasattr(pr, 'plant_id') else pr["plant_id"],
                    role=pr.role if hasattr(pr, 'role') else pr.get("role", "MEMBER")
                )
            )

    await db.commit()
    return success({"id": str(user.id), "username": user.username})


@router.get("")
async def list_users(
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import func as sql_func

    # 查询总数
    count_result = await db.execute(select(sql_func.count()).select_from(SysUser))
    total = count_result.scalar() or 0

    # 分页查询
    offset = (page - 1) * page_size
    result = await db.execute(
        select(SysUser).order_by(SysUser.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    user_list = []
    for user in users:
        info = await _build_user_response(db, user)
        user_list.append(info)

    return success({
        "list": user_list,
        "total": total
    })


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SysUser).where(SysUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return success(await _build_user_response(db, user))


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    current_user: SysUser = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SysUser).where(SysUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if data.real_name is not None:
        user.real_name = data.real_name
    if data.email is not None:
        user.email = data.email
    if data.mobile is not None:
        user.mobile = data.mobile
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.is_superadmin is not None:
        user.is_superadmin = data.is_superadmin

    if data.role_ids is not None:
        await db.execute(delete(user_role).where(user_role.c.user_id == user_id))
        for role_id in data.role_ids:
            await db.execute(
                user_role.insert().values(user_id=user.id, role_id=role_id)
            )

    if data.plant_ids is not None or data.plant_roles is not None:
        await db.execute(delete(user_plant).where(user_plant.c.user_id == user_id))
        plant_roles = data.plant_roles or []
        if not plant_roles and data.plant_ids:
            plant_roles = [{"plant_id": pid, "role": "MEMBER"} for pid in data.plant_ids]
        if plant_roles and not user.is_superadmin:
            for pr in plant_roles:
                await db.execute(
                    user_plant.insert().values(
                        user_id=user.id,
                        plant_id=pr.plant_id if hasattr(pr, 'plant_id') else pr["plant_id"],
                        role=pr.role if hasattr(pr, 'role') else pr.get("role", "MEMBER")
                    )
                )

    await db.commit()
    return success({"id": str(user.id), "username": user.username})


@router.patch("/{user_id}/status")
async def toggle_user_status(
    user_id: str,
    current_user: SysUser = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SysUser).where(SysUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.is_active = not user.is_active
    await db.commit()

    return success({
        "id": str(user.id),
        "username": user.username,
        "is_active": user.is_active
    })


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: SysUser = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SysUser).where(SysUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否有关联的巡检记录
    inspection_result = await db.execute(
        select(Inspection).where(Inspection.inspector_id == user_id).limit(1)
    )
    if inspection_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该用户已有关联的巡检记录，无法删除")

    # 检查是否有关联的异常单
    exception_result = await db.execute(
        select(ExceptionTicket).where(ExceptionTicket.current_assignee_id == user_id).limit(1)
    )
    if exception_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该用户已有关联的异常单，无法删除")

    await db.execute(delete(user_role).where(user_role.c.user_id == user_id))
    await db.execute(delete(user_plant).where(user_plant.c.user_id == user_id))
    await db.delete(user)
    await db.commit()

    return success({"id": user_id})