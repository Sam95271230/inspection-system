"""
用户、角色、权限相关模型
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


# 用户-角色 多对多关联表
user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("sys_user.id"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("role.id"), primary_key=True),
)


# 用户-厂区 数据权限关联表
user_plant = Table(
    "user_plant",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("sys_user.id"), primary_key=True),
    Column("plant_id", UUID(as_uuid=True), ForeignKey("plant.id"), primary_key=True),
)


class Role(Base):
    __tablename__ = "role"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(32), nullable=False, unique=True)
    name = Column(String(64), nullable=False)
    description = Column(String(255))


class SysUser(Base):
    __tablename__ = "sys_user"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(64), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(64))
    mobile = Column(String(20))
    is_active = Column(Boolean, default=True)
    is_superadmin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
