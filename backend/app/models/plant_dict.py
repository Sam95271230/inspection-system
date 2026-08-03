"""
厂区、线别、站别字典表
"""

import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Plant(Base):
    __tablename__ = "plant"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(32), nullable=False, unique=True)
    name = Column(String(64), nullable=False)

    lines = relationship("Line", back_populates="plant")


class Line(Base):
    __tablename__ = "line"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plant_id = Column(UUID(as_uuid=True), ForeignKey("plant.id"), nullable=False)
    code = Column(String(32), nullable=False)
    name = Column(String(64), nullable=False)

    plant = relationship("Plant", back_populates="lines")
    stations = relationship("Station", back_populates="line")


class Station(Base):
    __tablename__ = "station"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    line_id = Column(UUID(as_uuid=True), ForeignKey("line.id"), nullable=False)
    code = Column(String(32), nullable=False)
    name = Column(String(64), nullable=False)

    line = relationship("Line", back_populates="stations")
