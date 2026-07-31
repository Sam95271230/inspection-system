"""
巡检记录相关模型
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Inspection(Base):
    __tablename__ = "inspection"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    serial_no = Column(String(32), unique=True)
    plant_id = Column(UUID(as_uuid=True), ForeignKey("plant.id"), nullable=False)
    line_id = Column(UUID(as_uuid=True), ForeignKey("line.id"), nullable=False)
    station_id = Column(UUID(as_uuid=True), ForeignKey("station.id"), nullable=False)
    ip_address = Column(String(15), nullable=False)
    antivirus_status = Column(String(32), nullable=False)
    domain_status = Column(String(32), nullable=False)
    remark = Column(Text)
    status = Column(String(32), default="SUBMITTED")
    inspector_id = Column(UUID(as_uuid=True), ForeignKey("sys_user.id"), nullable=False)
    inspect_time = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = relationship("InspectionImage", back_populates="inspection", cascade="all, delete-orphan")


class InspectionImage(Base):
    __tablename__ = "inspection_image"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inspection_id = Column(UUID(as_uuid=True), ForeignKey("inspection.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    storage_key = Column(String(512), nullable=False)
    file_size = Column(String(64))
    mime_type = Column(String(64))
    sort_order = Column(String(64), default="0")

    inspection = relationship("Inspection", back_populates="images")
