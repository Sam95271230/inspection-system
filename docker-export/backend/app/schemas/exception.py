from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ExceptionAction(BaseModel):
    remark: Optional[str] = None
    assignee_id: Optional[str] = None
    attachment_urls: Optional[List[str]] = []


class ExceptionHistoryOut(BaseModel):
    id: str
    from_status: Optional[str]
    to_status: str
    operator_id: str
    operator_name: Optional[str]
    action: str
    remark: Optional[str]
    attachment_urls: Optional[List[str]]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
