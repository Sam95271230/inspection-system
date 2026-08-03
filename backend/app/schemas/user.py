from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID
from typing import Optional, List


class PlantRole(BaseModel):
    plant_id: str
    role: str  # MEMBER / LEADER


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
    plant_ids: List[str] = []  # 向后兼容
    plant_roles: List[PlantRole] = []


class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    is_active: Optional[bool] = None
    is_superadmin: Optional[bool] = None
    role_ids: Optional[List[str]] = None
    plant_ids: Optional[List[str]] = None  # 向后兼容
    plant_roles: Optional[List[PlantRole]] = None


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    real_name: Optional[str] = None
    mobile: Optional[str] = None
    is_active: bool
    is_superadmin: bool

    @field_validator('id', mode='before')
    @classmethod
    def coerce_id(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return str(v)


class UserOut(UserInfo):
    role_ids: List[str] = []
    plant_ids: List[str] = []
    plant_roles: List[PlantRole] = []