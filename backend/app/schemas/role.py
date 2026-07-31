from pydantic import BaseModel


class RoleCreate(BaseModel):
    code: str
    name: str
    description: str = ""


class RoleOut(RoleCreate):
    id: str

    class Config:
        from_attributes = True
