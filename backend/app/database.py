"""
数据库连接配置
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 从环境变量读取数据库 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://inspection_user:inspection_pass@postgres:5432/inspection_db"
)

# 创建异步引擎
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# 创建异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# ORM 基类
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    FastAPI 依赖：获取数据库会话
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
