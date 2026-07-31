from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.plant_dict import Plant, Line, Station
from app.utils.response import success
from app.schemas.plant_dict import PlantTreeOut, LineOut, StationOut

router = APIRouter(prefix="/dict", tags=["厂区字典"])


@router.get("/tree")
async def get_plant_dict_tree(db: AsyncSession = Depends(get_db)):
    """
    获取厂区-线别-站别树形结构
    """
    # 查询所有厂区
    plant_result = await db.execute(select(Plant))
    plants = plant_result.scalars().all()

    # 查询所有线别
    line_result = await db.execute(select(Line))
    lines = line_result.scalars().all()

    # 查询所有站别
    station_result = await db.execute(select(Station))
    stations = station_result.scalars().all()

    # 组装树
    tree = []
    for plant in plants:
        plant_data = {
            "id": str(plant.id),
            "code": plant.code,
            "name": plant.name,
            "children": []
        }
        for line in lines:
            if line.plant_id == plant.id:
                line_data = {
                    "id": str(line.id),
                    "plant_id": str(line.plant_id),
                    "code": line.code,
                    "name": line.name,
                    "children": []
                }
                for station in stations:
                    if station.line_id == line.id:
                        line_data["children"].append({
                            "id": str(station.id),
                            "line_id": str(station.line_id),
                            "code": station.code,
                            "name": station.name
                        })
                plant_data["children"].append(line_data)
        tree.append(plant_data)

    return success(data=tree)


@router.get("/lines")
async def get_lines(plant_id: str, db: AsyncSession = Depends(get_db)):
    """
    根据厂区 ID 查询线别
    """
    result = await db.execute(
        select(Line).where(Line.plant_id == plant_id)
    )
    lines = result.scalars().all()
    return success(data=[
        {"id": str(l.id), "plant_id": str(l.plant_id), "code": l.code, "name": l.name}
        for l in lines
    ])


@router.get("/stations")
async def get_stations(line_id: str, db: AsyncSession = Depends(get_db)):
    """
    根据线别 ID 查询站别
    """
    result = await db.execute(
        select(Station).where(Station.line_id == line_id)
    )
    stations = result.scalars().all()
    return success(data=[
        {"id": str(s.id), "line_id": str(s.line_id), "code": s.code, "name": s.name}
        for s in stations
    ])
