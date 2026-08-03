"""
厂区、线别、站别字典表
"""

import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Plant(Base):
    __tablename__ = "plant"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(32), nullable=False, unique=True)
    name = Column(String(64), nullable=False)


class Line(Base):
    __tablename__ = "line"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plant_id = Column(UUID(as_uuid=True), ForeignKey("plant.id"), nullable=False)
    code = Column(String(32), nullable=False)
    name = Column(String(64), nullable=False)


class Station(Base):
    __tablename__ = "station"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    line_id = Column(UUID(as_uuid=True), ForeignKey("line.id"), nullable=False)
    code = Column(String(32), nullable=False)
    name = Column(String(64), nullable=False)
