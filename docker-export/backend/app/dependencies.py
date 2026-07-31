from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import SysUser, user_plant
from app.utils.jwt_util import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> SysUser:
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 无效")

    result = await db.execute(select(SysUser).where(SysUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")

    return user


async def require_superadmin(
    current_user: SysUser = Depends(get_current_user)
) -> SysUser:
    """
    校验当前用户是否为超级管理员
    """
    if not current_user.is_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅超级管理员可操作")
    return current_user


async def get_authorized_plant_ids(
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list:
    if current_user.is_superadmin:
        return []

    result = await db.execute(
        select(user_plant.c.plant_id).where(user_plant.c.user_id == current_user.id)
    )
    return [str(row[0]) for row in result.all()]
