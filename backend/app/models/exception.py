import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class ExceptionTicket(Base):
    __tablename__ = "exception_ticket"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inspection_id = Column(UUID(as_uuid=True), ForeignKey("inspection.id"), nullable=False, unique=True)
    plant_id = Column(UUID(as_uuid=True), ForeignKey("plant.id"), nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(String(32), default="PENDING")
    current_assignee_id = Column(UUID(as_uuid=True), ForeignKey("sys_user.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ExceptionHistory(Base):
    __tablename__ = "exception_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("exception_ticket.id"), nullable=False)
    from_status = Column(String(32))
    to_status = Column(String(32), nullable=False)
    operator_id = Column(UUID(as_uuid=True), ForeignKey("sys_user.id"), nullable=False)
    action = Column(String(64), nullable=False)
    remark = Column(Text)
    attachment_urls = Column(ARRAY(String))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
