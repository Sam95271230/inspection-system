from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import io

from openpyxl import load_workbook

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


@router.post("/import")
async def import_plant_dict(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    批量导入厂区/线别/站别数据（Excel 文件）
    
    Excel 格式（第一行为表头，从第二行开始读取）：
    | 厂区代码 | 厂区名称 | 线别代码 | 线别名称 | 站别代码 | 站别名称 |
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        return success(code=400, message="仅支持 Excel 文件（.xlsx / .xls）")

    content = await file.read()
    wb = load_workbook(io.BytesIO(content), data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(min_row=2, values_only=True))  # 跳过表头

    stats = {"plant": 0, "line": 0, "station": 0}
    plant_cache = {}   # code -> Plant
    line_cache = {}    # (plant_code, line_code) -> Line

    for row in rows:
        plant_code = str(row[0]).strip() if row[0] else None
        plant_name = str(row[1]).strip() if row[1] else None
        line_code = str(row[2]).strip() if row[2] else None
        line_name = str(row[3]).strip() if row[3] else None
        station_code = str(row[4]).strip() if row[4] else None
        station_name = str(row[5]).strip() if row[5] else None

        if not plant_code or not plant_name:
            continue  # 跳过空行

        # 厂区：如果 code 不存在则创建
        if plant_code not in plant_cache:
            existing = await db.execute(select(Plant).where(Plant.code == plant_code))
            plant = existing.scalar_one_or_none()
            if not plant:
                plant = Plant(code=plant_code, name=plant_name)
                db.add(plant)
                await db.flush()
                stats["plant"] += 1
            plant_cache[plant_code] = plant
        else:
            plant = plant_cache[plant_code]

        # 线别
        if line_code and line_name:
            line_key = f"{plant_code}|{line_code}"
            if line_key not in line_cache:
                existing_line = await db.execute(
                    select(Line).where(Line.plant_id == plant.id, Line.code == line_code)
                )
                line = existing_line.scalar_one_or_none()
                if not line:
                    line = Line(plant_id=plant.id, code=line_code, name=line_name)
                    db.add(line)
                    await db.flush()
                    stats["line"] += 1
                line_cache[line_key] = line
            else:
                line = line_cache[line_key]

            # 站别
            if station_code and station_name:
                existing_station = await db.execute(
                    select(Station).where(Station.line_id == line.id, Station.code == station_code)
                )
                station = existing_station.scalar_one_or_none()
                if not station:
                    station = Station(line_id=line.id, code=station_code, name=station_name)
                    db.add(station)
                    stats["station"] += 1

    await db.commit()

    return success({
        "message": f"导入完成：新增厂区 {stats['plant']} 个，线别 {stats['line']} 个，站别 {stats['station']} 个",
        "stats": stats
    })