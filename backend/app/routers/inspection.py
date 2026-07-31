from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from datetime import datetime
import uuid as uuid_module
import os
import io
from urllib.parse import quote

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import OneCellAnchor, AnchorMarker
from openpyxl.drawing.geometry import Ext
from PIL import Image

from app.database import get_db
from app.models.inspection import Inspection, InspectionImage
from app.models.exception import ExceptionTicket
from app.models.user import SysUser
from app.models.plant_dict import Plant, Line, Station
from app.utils.response import success
from app.schemas.inspection import InspectionCreate
from app.utils.minio_client import upload_file, get_minio_client
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


# 状态中文映射
STATUS_LABEL_MAP = {
    "NORMAL": "正常",
    "ABNORMAL": "异常",
    "NOT_INSTALLED": "未安装",
    "JOINED": "已入域",
    "NOT_JOINED": "未入域",
    "NOT_APPLICABLE": "不适用",
}


def _build_inspection_query(
    stmt,
    plant_id: str = None,
    line_id: str = None,
    station_id: str = None,
    start_time: str = None,
    end_time: str = None,
    antivirus_status: str = None,
    domain_status: str = None,
):
    """构建巡检记录查询的通用筛选条件"""
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
    return stmt


@router.get("/export")
async def export_inspections(
    plant_id: str = Query(None),
    line_id: str = Query(None),
    station_id: str = Query(None),
    start_time: str = Query(None),
    end_time: str = Query(None),
    antivirus_status: str = Query(None),
    domain_status: str = Query(None),
    current_user: SysUser = Depends(get_current_user),
    authorized_plant_ids: list = Depends(get_authorized_plant_ids),
    db: AsyncSession = Depends(get_db),
):
    """导出巡检记录为 Excel 文件"""
    # 联表查询：巡检记录 + 厂区/线别/站别 + 巡检人
    stmt = (
        select(Inspection)
        .options(
            joinedload(Inspection.images),
        )
        .order_by(Inspection.created_at.desc())
    )

    # 厂区权限过滤
    if not current_user.is_superadmin:
        if not authorized_plant_ids:
            stmt = stmt.where(Inspection.plant_id.in_([]))
        else:
            stmt = stmt.where(Inspection.plant_id.in_(authorized_plant_ids))

    stmt = _build_inspection_query(
        stmt,
        plant_id=plant_id,
        line_id=line_id,
        station_id=station_id,
        start_time=start_time,
        end_time=end_time,
        antivirus_status=antivirus_status,
        domain_status=domain_status,
    )

    result = await db.execute(stmt)
    inspections = result.unique().scalars().all()

    # 收集关联 ID 并批量查询名称
    plant_ids = list({i.plant_id for i in inspections})
    line_ids = list({i.line_id for i in inspections})
    station_ids = list({i.station_id for i in inspections})
    inspector_ids = list({i.inspector_id for i in inspections})

    plant_name_map = {}
    if plant_ids:
        plant_result = await db.execute(select(Plant).where(Plant.id.in_(plant_ids)))
        for p in plant_result.scalars().all():
            plant_name_map[str(p.id)] = f"{p.code} - {p.name}"

    line_name_map = {}
    if line_ids:
        line_result = await db.execute(select(Line).where(Line.id.in_(line_ids)))
        for l in line_result.scalars().all():
            line_name_map[str(l.id)] = f"{l.code} - {l.name}"

    station_name_map = {}
    if station_ids:
        station_result = await db.execute(select(Station).where(Station.id.in_(station_ids)))
        for s in station_result.scalars().all():
            station_name_map[str(s.id)] = f"{s.code} - {s.name}"

    inspector_name_map = {}
    if inspector_ids:
        user_result = await db.execute(select(SysUser).where(SysUser.id.in_(inspector_ids)))
        for u in user_result.scalars().all():
            inspector_name_map[str(u.id)] = u.real_name or u.username

    # 创建 Excel 工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "巡检记录"

    # 样式定义
    header_font = Font(name="微软雅黑", bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    cell_alignment = Alignment(horizontal="center", vertical="center")
    cell_alignment_left = Alignment(horizontal="left", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # 表头（新增"巡检证据"列）
    headers = ["巡检单号", "厂区", "线别", "站别", "IP地址", "防毒软件状态", "入域状态", "备注", "巡检时间", "巡检人", "巡检证据"]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # 初始化 MinIO 客户端（用于下载巡检证据图片）
    minio_client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET", "inspection-images")

    # 图片嵌入配置
    IMG_TARGET_HEIGHT = 90  # 像素，图片缩放后的高度
    IMAGES_PER_ROW = 3      # 每行最多并排 3 张图片
    IMG_GAP_PX = 4          # 图片间距（像素）
    # 将像素宽度近似换算为 Excel 列宽单位（1 单位 ≈ 7 像素）
    IMG_EMBED_WIDTH = (IMG_TARGET_HEIGHT * IMAGES_PER_ROW + IMG_GAP_PX * (IMAGES_PER_ROW + 1)) / 7.0

    # 数据行
    for row_idx, inspection in enumerate(inspections, 2):
        values = [
            inspection.serial_no,
            plant_name_map.get(str(inspection.plant_id), ""),
            line_name_map.get(str(inspection.line_id), ""),
            station_name_map.get(str(inspection.station_id), ""),
            inspection.ip_address,
            STATUS_LABEL_MAP.get(inspection.antivirus_status, inspection.antivirus_status),
            STATUS_LABEL_MAP.get(inspection.domain_status, inspection.domain_status),
            inspection.remark or "",
            inspection.inspect_time.strftime("%Y-%m-%d %H:%M:%S") if inspection.inspect_time else "",
            inspector_name_map.get(str(inspection.inspector_id), ""),
        ]
        # 写入前 10 列文本数据
        for col_idx, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = Font(name="微软雅黑", size=10)
            cell.border = thin_border
            if col_idx in (8,):  # 备注列左对齐
                cell.alignment = cell_alignment_left
            else:
                cell.alignment = cell_alignment

        # 第 11 列：嵌入巡检证据图片
        evidence_cell = ws.cell(row=row_idx, column=11)
        evidence_cell.border = thin_border
        evidence_cell.alignment = Alignment(horizontal="center", vertical="top")

        images = inspection.images
        if images:
            # 计算该行的高度（根据图片行数）
            img_rows_count = (len(images) + IMAGES_PER_ROW - 1) // IMAGES_PER_ROW
            row_height_px = img_rows_count * (IMG_TARGET_HEIGHT + IMG_GAP_PX) + IMG_GAP_PX
            ws.row_dimensions[row_idx].height = row_height_px * 0.75  # 像素转磅（约 0.75）

            for img_idx, inspection_image in enumerate(images):
                try:
                    # 从 MinIO 下载图片
                    img_obj = minio_client.get_object(bucket_name, inspection_image.storage_key)
                    img_bytes = img_obj.read()
                    img_obj.close()
                    img_obj.release_conn()

                    # 用 Pillow 处理图片：缩放并转为 JPEG
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    pil_img = pil_img.convert("RGB")
                    w, h = pil_img.size
                    new_w = int(w * IMG_TARGET_HEIGHT / h)
                    pil_img = pil_img.resize((new_w, IMG_TARGET_HEIGHT), Image.LANCZOS)

                    img_stream = io.BytesIO()
                    pil_img.save(img_stream, format="JPEG", quality=85)
                    img_stream.seek(0)

                    # 计算图片在单元格中的锚点位置
                    img_col = img_idx % IMAGES_PER_ROW
                    img_row = img_idx // IMAGES_PER_ROW
                    offset_x = IMG_GAP_PX + img_col * (IMG_TARGET_HEIGHT + IMG_GAP_PX)
                    offset_y = IMG_GAP_PX + img_row * (IMG_TARGET_HEIGHT + IMG_GAP_PX)

                    # 创建 openpyxl 图片对象并嵌入
                    xl_img = XLImage(img_stream)
                    xl_img.width = new_w
                    xl_img.height = IMG_TARGET_HEIGHT

                    # 锚点：列偏移量（EMU，1像素 = 9525 EMU）
                    col_offset = int(offset_x * 9525)
                    row_offset = int(offset_y * 9525)

                    xl_img.anchor = OneCellAnchor(
                        _from=AnchorMarker(
                            col=10,  # 第 11 列（从 0 开始）
                            colOff=col_offset,
                            row=row_idx - 1,
                            rowOff=row_offset,
                        ),
                        ext=Ext(new_w * 9525, IMG_TARGET_HEIGHT * 9525),
                    )

                    ws.add_image(xl_img)
                except Exception:
                    # 图片下载失败时写入占位文字
                    evidence_cell.value = (evidence_cell.value or "") + f"[图片加载失败] "
        else:
            evidence_cell.value = "无"
            ws.row_dimensions[row_idx].height = 30

    # 设置列宽（第 11 列为巡检证据图片列）
    column_widths = [20, 22, 22, 22, 16, 16, 12, 30, 22, 14, IMG_EMBED_WIDTH]
    for col_idx, width in enumerate(column_widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = width

    # 冻结首行
    ws.freeze_panes = "A2"

    # 写入内存流
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"巡检记录_{datetime.now().strftime('%Y%m%d')}.xlsx"
    # filename*=UTF-8'' 要求对中文文件名做百分号编码，因为 HTTP 头值必须为 latin-1 安全
    encoded_filename = quote(filename, safe='')

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )
