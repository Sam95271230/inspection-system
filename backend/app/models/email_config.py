import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class EmailConfig(Base):
    """邮件配置（单行配置表）"""
    __tablename__ = "email_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    smtp_host = Column(String(255), default="")
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(255), default="")
    smtp_password = Column(String(255), default="")
    smtp_use_tls = Column(Boolean, default=True)
    from_name = Column(String(128), default="巡检系统")
    enabled = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)