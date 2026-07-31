from pydantic import BaseModel
from typing import List


class PlantOut(BaseModel):
    id: str
    code: str
    name: str


class LineOut(BaseModel):
    id: str
    plant_id: str
    code: str
    name: str


class StationOut(BaseModel):
    id: str
    line_id: str
    code: str
    name: str


class PlantTreeOut(PlantOut):
    children: List['LineTreeOut'] = []


class LineTreeOut(LineOut):
    children: List[StationOut] = []


PlantTreeOut.model_rebuild()
LineTreeOut.model_rebuild()
