"""
认证相关路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import os

from app.database import get_db
from app.models.user import SysUser
from app.security.password import verify_password, get_password_hash
from app.utils.jwt_util import create_access_token
from app.utils.response import success
from app.schemas.user import UserInfo, UserCreate
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录接口，接收 JSON 格式：username, password
    """
    result = await db.execute(
        select(SysUser).where(SysUser.username == data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="账号已被禁用")

    access_token = create_access_token({"sub": str(user.id)})

    return success({
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "real_name": user.real_name,
            "is_superadmin": user.is_superadmin,
        }
    })


@router.get("/me", response_model=UserInfo)
async def get_me(
    current_user: SysUser = Depends(get_current_user),
):
    """
    获取当前登录用户信息
    """
    return current_user


@router.post("/init-admin")
async def init_admin(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    初始化管理员账号，仅用于首次部署。
    通过环境变量 ALLOW_INIT_ADMIN=true 启用，初始化后应关闭。
    """
    if os.getenv("ALLOW_INIT_ADMIN", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="初始化管理员功能未启用，请设置 ALLOW_INIT_ADMIN=true")

    # 如果已存在任何管理员，则拒绝再次初始化
    existing_admin = await db.execute(
        select(SysUser).where(SysUser.is_superadmin.is_(True)).limit(1)
    )
    if existing_admin.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已存在管理员账号，请通过用户管理页面创建新用户")

    result = await db.execute(select(SysUser).where(SysUser.username == data.username))
    if result.scalar_one_or_none():
        return {"code": 400, "message": "用户已存在", "data": None}

    user = SysUser(
        username=data.username,
        password_hash=get_password_hash(data.password),
        real_name=data.real_name or data.username,
        is_active=True,
        is_superadmin=True,
    )
    db.add(user)
    await db.commit()
    return success({"id": str(user.id), "username": user.username})
