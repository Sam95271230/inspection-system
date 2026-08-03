"""
邮件模板
"""
import os
from app.constants import EXCEPTION_STATUS_MAP


def build_exception_email_body(
    ticket,
    operator,
    inspection_images: list,
    serial_no: str,
    ip: str,
    plant_name: str,
) -> str:
    """构建异常单邮件通知的 HTML 正文"""
    system_url = os.getenv("SYSTEM_URL", "http://localhost:8081")
    ticket_url = f"{system_url}/exceptions"
    operator_name = operator.real_name or operator.username

    # 图片HTML
    imgs_html = "<p><b>巡检证据图片：</b></p><div style='display:flex;flex-wrap:wrap;gap:8px;'>"
    if inspection_images:
        for img in inspection_images:
            imgs_html += f'<img src="{img["url"]}" style="width:200px;border:1px solid #ddd;border-radius:4px;" alt="{img["file_name"]}"/>'
    else:
        imgs_html += "<span style='color:#999;'>暂无图片</span>"
    imgs_html += "</div>"

    body = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 640px;">
    <h3 style="color: #409EFF;">巡检系统 - 异常单状态更新</h3>
    <table border="1" cellpadding="10" cellspacing="0" style="border-collapse:collapse; width:100%; border-color:#e4e7ed;">
      <tr><td style="background:#f5f7fa; width:120px;"><b>巡检单号</b></td><td>{serial_no}</td></tr>
      <tr><td style="background:#f5f7fa;"><b>IP 地址</b></td><td>{ip}</td></tr>
      <tr><td style="background:#f5f7fa;"><b>厂区</b></td><td>{plant_name}</td></tr>
      <tr><td style="background:#f5f7fa;"><b>异常摘要</b></td><td style="color:#e6a23c;font-weight:600;">{ticket.title}</td></tr>
      <tr><td style="background:#f5f7fa;"><b>当前状态</b></td><td>{EXCEPTION_STATUS_MAP.get(ticket.status, ticket.status)}</td></tr>
      <tr><td style="background:#f5f7fa;"><b>操作人</b></td><td>{operator_name}</td></tr>
    </table>
    {imgs_html}
    <div style="margin-top:20px; padding:16px; background:#ecf5ff; border-radius:6px;">
      <p style="margin:0; font-size:14px;">
        <a href="{ticket_url}" style="color:#409EFF; font-weight:bold; text-decoration:none;">
          点击查看工单详情 &raquo;
        </a>
      </p>
      <p style="margin:8px 0 0 0; color:#909399; font-size:12px;">或复制链接：{ticket_url}</p>
    </div>
    <p style="margin-top:20px; color:#909399; font-size:12px;">此邮件由产线电脑巡检系统自动发送，请勿回复。</p>
    </body></html>
    """
    return body
