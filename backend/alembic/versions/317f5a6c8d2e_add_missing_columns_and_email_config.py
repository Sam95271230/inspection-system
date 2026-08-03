"""add missing columns and email_config

Revision ID: 317f5a6c8d2e
Revises: 210fb62aebc3
Create Date: 2026-08-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '317f5a6c8d2e'
down_revision = '210fb62aebc3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. sys_user 添加 email 列（幂等）
    op.execute("ALTER TABLE sys_user ADD COLUMN IF NOT EXISTS email VARCHAR(128)")

    # 2. user_plant 添加 role 列（幂等）
    op.execute("ALTER TABLE user_plant ADD COLUMN IF NOT EXISTS role VARCHAR(16) DEFAULT 'MEMBER'")

    # 3. inspection 添加 machine_name 列（幂等）
    op.execute("ALTER TABLE inspection ADD COLUMN IF NOT EXISTS machine_name VARCHAR(128)")

    # 4. inspection 添加 inspector_name 列（幂等）
    op.execute("ALTER TABLE inspection ADD COLUMN IF NOT EXISTS inspector_name VARCHAR(64)")

    # 5. 创建 email_config 表（幂等）
    op.execute("""
        CREATE TABLE IF NOT EXISTS email_config (
            id UUID NOT NULL DEFAULT uuid_generate_v4(),
            smtp_host VARCHAR(255) DEFAULT '',
            smtp_port INTEGER DEFAULT 587,
            smtp_user VARCHAR(255) DEFAULT '',
            smtp_password VARCHAR(255) DEFAULT '',
            smtp_use_tls BOOLEAN DEFAULT true,
            from_name VARCHAR(128) DEFAULT '巡检系统',
            enabled BOOLEAN DEFAULT false,
            updated_at TIMESTAMP WITHOUT TIME ZONE,
            PRIMARY KEY (id)
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS email_config")
    op.execute("ALTER TABLE inspection DROP COLUMN IF EXISTS inspector_name")
    op.execute("ALTER TABLE inspection DROP COLUMN IF EXISTS machine_name")
    op.execute("ALTER TABLE user_plant DROP COLUMN IF EXISTS role")
    op.execute("ALTER TABLE sys_user DROP COLUMN IF EXISTS email")
