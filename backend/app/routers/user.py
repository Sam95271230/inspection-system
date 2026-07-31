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

    if data.plant_ids and not data.is_superadmin:
        for plant_id in data.plant_ids:
            await db.execute(
                user_plant.insert().values(user_id=user.id, plant_id=plant_id)
            )

    await db.commit()
    return success({"id": str(user.id), "username": user.username})


@router.get("")
async def list_users(
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SysUser).order_by(SysUser.created_at.desc()))
    users = result.scalars().all()

    user_list = []
    for user in users:
        role_result = await db.execute(
            select(user_role.c.role_id).where(user_role.c.user_id == user.id)
        )
        plant_result = await db.execute(
            select(user_plant.c.plant_id).where(user_plant.c.user_id == user.id)
        )

        user_list.append({
            "id": str(user.id),
            "username": user.username,
            "real_name": user.real_name,
            "mobile": user.mobile,
            "is_active": user.is_active,
            "is_superadmin": user.is_superadmin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "role_ids": [str(r[0]) for r in role_result.all()],
            "plant_ids": [str(p[0]) for p in plant_result.all()],
        })

    return success({
        "list": user_list,
        "total": len(user_list)
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

    role_result = await db.execute(
        select(user_role.c.role_id).where(user_role.c.user_id == user.id)
    )
    plant_result = await db.execute(
        select(user_plant.c.plant_id).where(user_plant.c.user_id == user.id)
    )

    return success({
        "id": str(user.id),
        "username": user.username,
        "real_name": user.real_name,
        "mobile": user.mobile,
        "is_active": user.is_active,
        "is_superadmin": user.is_superadmin,
        "role_ids": [str(r[0]) for r in role_result.all()],
        "plant_ids": [str(p[0]) for p in plant_result.all()],
    })


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

    if data.plant_ids is not None:
        await db.execute(delete(user_plant).where(user_plant.c.user_id == user_id))
        if not user.is_superadmin:
            for plant_id in data.plant_ids:
                await db.execute(
                    user_plant.insert().values(user_id=user.id, plant_id=plant_id)
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
