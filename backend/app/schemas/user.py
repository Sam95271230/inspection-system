from pydantic import BaseModel, Field
from typing import Optional, List


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=3, max_length=64)


class UserCreate(BaseModel):
    username: str
    password: str
    real_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    is_active: bool = True
    is_superadmin: bool = False
    role_ids: List[str] = []
    plant_ids: List[str] = []


class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    is_active: Optional[bool] = None
    is_superadmin: Optional[bool] = None
    role_ids: Optional[List[str]] = None
    plant_ids: Optional[List[str]] = None


class UserInfo(BaseModel):
    id: str
    username: str
    real_name: Optional[str] = None
    mobile: Optional[str] = None
    is_active: bool
    is_superadmin: bool

    class Config:
        from_attributes = True


class UserOut(UserInfo):
    role_ids: List[str] = []
    plant_ids: List[str] = []
