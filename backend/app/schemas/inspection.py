from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID
from typing import Optional, List
from datetime import datetime


class InspectionCreate(BaseModel):
    plant_id: str
    line_id: str
    station_id: str
    ip_address: str = Field(..., pattern=r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    machine_name: Optional[str] = None
    antivirus_status: str
    domain_status: str
    remark: Optional[str] = None
    status: Optional[str] = "SUBMITTED"
    inspect_time: Optional[str] = None
    inspector_name: Optional[str] = None
    images: Optional[List[dict]] = []


class InspectionOut(InspectionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    serial_no: str
    inspector_id: str
    inspect_time: datetime

    @field_validator('id', 'inspector_id', mode='before')
    @classmethod
    def coerce_uuid(cls, v):
        return str(v) if v is not None else v
