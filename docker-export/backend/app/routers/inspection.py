from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid as uuid_module
import os

from app.database import get_db
from app.models.inspection import Inspection, InspectionImage
from app.models.exception import ExceptionTicket
from app.models.user import SysUser
from app.models.plant_dict import Plant
from app.utils.response import success
from app.schemas.inspection import InspectionCreate
from app.utils.minio_client import upload_file
from app.dependencies import get_current_user, get_authorized_plant_ids

router = APIRouter(prefix="/inspections", tags=["巡检记录"])


@router.post("")
async def create_inspection(
    data: InspectionCreate,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    today = datetime.now().strftime("%Y%m%d")
    serial_no = f"INS-{today}-{uuid_module.uuid4().hex[:4].upper()}"

    inspection = Inspection(
        serial_no=serial_no,
        plant_id=data.plant_id,
        line_id=data.line_id,
        station_id=data.station_id,
        ip_address=data.ip_address,
        antivirus_status=data.antivirus_status,
        domain_status=data.domain_status,
        remark=data.remark,
        status=data.status,
        inspector_id=current_user.id
    )
    db.add(inspection)
    await db.flush()

    for img in (data.images or []):
        image = InspectionImage(
            inspection_id=inspection.id,
            file_name=img.get("name", "image.jpg"),
            storage_key=img.get("storage_key", ""),
            mime_type=img.get("mime_type", "image/jpeg")
        )
        db.add(image)

    # 异常自动建单
    if data.antivirus_status == "ABNORMAL" or data.domain_status == "NOT_JOINED":
        plant_result = await db.execute(select(Plant).where(Plant.id == data.plant_id))
        plant = plant_result.scalar_one_or_none()

        title_parts = []
        if data.antivirus_status == "ABNORMAL":
            title_parts.append("防毒软件异常")
        if data.domain_status == "NOT_JOINED":
            title_parts.append("未入域")
        title = " - ".join(title_parts)

        exception_ticket = ExceptionTicket(
            inspection_id=inspection.id,
            plant_id=data.plant_id,
            title=title,
            status="PENDING"
        )
        db.add(exception_ticket)

    await db.commit()

    return success({"id": str(inspection.id), "serial_no": serial_no})


@router.get("")
async def list_inspections(
    page: int = 1,
    page_size: int = 10,
    plant_id: str = None,
    line_id: str = None,
    station_id: str = None,
    start_time: str = None,
    end_time: str = None,
    antivirus_status: str = None,
    domain_status: str = None,
    current_user: SysUser = Depends(get_current_user),
    authorized_plant_ids: list = Depends(get_authorized_plant_ids),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Inspection).order_by(Inspection.created_at.desc())

    if not current_user.is_superadmin:
        if not authorized_plant_ids:
            return success({"list": [], "total": 0})
        stmt = stmt.where(Inspection.plant_id.in_(authorized_plant_ids))

    if plant_id:
        stmt = stmt.where(Inspection.plant_id == plant_id)
    if line_id:
        stmt = stmt.where(Inspection.line_id == line_id)
    if station_id:
        stmt = stmt.where(Inspection.station_id == station_id)
    if antivirus_status:
        stmt = stmt.where(Inspection.antivirus_status == antivirus_status)
    if domain_status:
        stmt = stmt.where(Inspection.domain_status == domain_status)
    if start_time:
        stmt = stmt.where(Inspection.inspect_time >= start_time)
    if end_time:
        stmt = stmt.where(Inspection.inspect_time <= end_time)

    offset = (page - 1) * page_size
    result = await db.execute(stmt.offset(offset).limit(page_size))
    inspections = result.scalars().all()

    inspection_ids = [i.id for i in inspections]
    images = []
    if inspection_ids:
        img_result = await db.execute(
            select(InspectionImage).where(InspectionImage.inspection_id.in_(inspection_ids))
        )
        images = img_result.scalars().all()

    image_map = {}
    for img in images:
        if str(img.inspection_id) not in image_map:
            image_map[str(img.inspection_id)] = []
        image_map[str(img.inspection_id)].append({
            "name": img.file_name,
            "url": f"{os.getenv('MINIO_EXTERNAL_URL', 'http://localhost:9000')}/{os.getenv('MINIO_BUCKET', 'inspection-images')}/{img.storage_key}",
            "storage_key": img.storage_key
        })

    return success({
        "list": [
            {
                "id": str(i.id),
                "serial_no": i.serial_no,
                "plant_id": str(i.plant_id),
                "line_id": str(i.line_id),
                "station_id": str(i.station_id),
                "ip_address": i.ip_address,
                "antivirus_status": i.antivirus_status,
                "domain_status": i.domain_status,
                "remark": i.remark,
                "status": i.status,
                "inspect_time": i.inspect_time.isoformat() if i.inspect_time else None,
                "images": image_map.get(str(i.id), [])
            }
            for i in inspections
        ],
        "total": len(inspections)
    })


@router.post("/upload")
async def upload_inspection_image(file: UploadFile = File(...)):
    content = await file.read()
    object_name = f"inspection/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    url = upload_file(object_name, content, file.content_type or "image/jpeg")
    return success({
        "url": url,
        "storage_key": object_name,
        "name": file.filename
    })
