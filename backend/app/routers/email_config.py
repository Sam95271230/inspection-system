import os
import smtplib
from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.email_config import EmailConfig
from app.models.user import SysUser
from app.utils.response import success
from app.dependencies import get_current_user, require_superadmin
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/email-config", tags=["邮件配置"])


class EmailConfigUpdate(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: Optional[str] = None  # 留空则不改
    smtp_use_tls: bool = True
    from_name: str = "巡检系统"
    enabled: bool = False


class TestEmailRequest(BaseModel):
    to_email: str


async def _get_config(db: AsyncSession):
    """获取或创建邮件配置（单行）"""
    result = await db.execute(select(EmailConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        config = EmailConfig()
        db.add(config)
        await db.flush()
    return config


async def get_active_email_config(db: AsyncSession):
    """获取启用的邮件配置，用于发邮件时调用"""
    result = await db.execute(select(EmailConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config or not config.enabled:
        return None
    return config


def _mask_password(pwd: str) -> str:
    if len(pwd) <= 4:
        return "****"
    return pwd[:2] + "****" + pwd[-2:]


def _send_email(config: EmailConfig, to_email: str, subject: str, body: str):
    """同步发送邮件，支持 TLS/SSL 两种模式"""
    msg = MIMEMultipart()
    # 中文发件人名称需 RFC 2047 编码
    msg["From"] = formataddr((config.from_name, config.smtp_user))
    msg["To"] = to_email
    msg["Subject"] = Header(subject, "utf-8")
    msg.attach(MIMEText(body, "html", "utf-8"))

    last_error = None

    # 尝试用户配置的加密方式
    modes = [(config.smtp_use_tls, config.smtp_port)]

    # 如果用户选 TLS(587)，也尝试 SSL(465) 作为备选
    if config.smtp_use_tls and config.smtp_port == 587:
        modes.append((False, 465))
    elif not config.smtp_use_tls and config.smtp_port == 465:
        modes.append((True, 587))

    for use_tls, port in modes:
        try:
            if use_tls:
                server = smtplib.SMTP(config.smtp_host, port, timeout=15)
                server.ehlo()
                if server.has_extn("STARTTLS"):
                    server.starttls()
                    server.ehlo()
                server.login(config.smtp_user, config.smtp_password)
            else:
                ctx = __import__('ssl').create_default_context()
                server = smtplib.SMTP_SSL(config.smtp_host, port, timeout=15, context=ctx)
                server.login(config.smtp_user, config.smtp_password)

            server.sendmail(config.smtp_user, [to_email], msg.as_string())
            server.quit()
            return  # 发送成功
        except Exception as e:
            last_error = str(e)
            try:
                server.quit()
            except Exception:
                pass
            continue

    raise Exception(last_error or "未知发送错误")


@router.get("")
async def get_email_config(
    current_user: SysUser = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db)
):
    config = await _get_config(db)
    return success({
        "id": str(config.id),
        "smtp_host": config.smtp_host,
        "smtp_port": config.smtp_port,
        "smtp_user": config.smtp_user,
        "smtp_password": _mask_password(config.smtp_password) if config.smtp_password else "",
        "smtp_password_set": bool(config.smtp_password),
        "smtp_use_tls": config.smtp_use_tls,
        "from_name": config.from_name,
        "enabled": config.enabled,
    })


@router.put("")
async def update_email_config(
    data: EmailConfigUpdate,
    current_user: SysUser = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db)
):
    config = await _get_config(db)

    config.smtp_host = data.smtp_host
    config.smtp_port = data.smtp_port
    config.smtp_user = data.smtp_user
    if data.smtp_password is not None and data.smtp_password != "":
        config.smtp_password = data.smtp_password
    config.smtp_use_tls = data.smtp_use_tls
    config.from_name = data.from_name
    config.enabled = data.enabled

    await db.commit()
    return success({"message": "邮件配置已保存"})


@router.post("/test")
async def test_email_config(
    data: TestEmailRequest,
    current_user: SysUser = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db)
):
    config = await _get_config(db)

    if not config.smtp_host or not config.smtp_user:
        raise HTTPException(status_code=400, detail="请先配置 SMTP 服务器信息")

    try:
        subject = "[巡检系统] 邮件测试"
        body = f"""
        <h3>邮件配置测试</h3>
        <p>这是一封来自<b>产线电脑巡检系统</b>的测试邮件。</p>
        <p>如果您收到此邮件，说明邮件配置已生效。</p>
        <hr/>
        <table border="0">
          <tr><td><b>SMTP 服务器</b></td><td>：{config.smtp_host}:{config.smtp_port}</td></tr>
          <tr><td><b>发送账号</b></td><td>：{config.smtp_user}</td></tr>
          <tr><td><b>发送时间</b></td><td>：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
        </table>
        """
        _send_email(config, data.to_email, subject, body)
        return success({"message": f"测试邮件已发送至 {data.to_email}，请查收"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"邮件发送失败：{str(e)}。请检查SMTP服务器、端口、账号和授权码是否正确。QQ邮箱需使用SMTP授权码而非密码。")
