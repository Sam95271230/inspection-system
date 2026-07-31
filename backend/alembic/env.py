"""
Alembic 迁移环境配置
"""

from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# 导入所有模型，让 Alembic 能识别
from app.database import Base
from app.models import user, plant_dict, inspection, exception  # noqa: F401

# 这是 Alembic Config 对象
config = context.config

# 解释配置文件中的 Python 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 模型 Base 的 metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """在线模式运行迁移"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())
