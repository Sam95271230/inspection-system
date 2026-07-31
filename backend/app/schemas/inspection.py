from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class InspectionCreate(BaseModel):
    plant_id: str
    line_id: str
    station_id: str
    ip_address: str = Field(..., pattern=r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    antivirus_status: str
    domain_status: str
    remark: Optional[str] = None
    status: Optional[str] = "SUBMITTED"
    images: Optional[List[dict]] = []


class InspectionOut(InspectionCreate):
    id: str
    serial_no: str
    inspector_id: str
    inspect_time: datetime

    class Config:
        from_attributes = True
