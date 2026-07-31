from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.models.user import Role, user_role
from app.utils.response import success
from app.schemas.role import RoleCreate, RoleOut

router = APIRouter(prefix="/roles", tags=["角色管理"])


@router.post("")
async def create_role(data: RoleCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role).where(Role.code == data.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="角色编码已存在")

    role = Role(code=data.code, name=data.name, description=data.description)
    db.add(role)
    await db.commit()
    return success({"id": str(role.id), "code": role.code})


@router.get("")
async def list_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role).order_by(Role.code))
    roles = result.scalars().all()
    return success([
        {"id": str(r.id), "code": r.code, "name": r.name, "description": r.description}
        for r in roles
    ])
