"""
全局常量
"""

# 状态中文映射
STATUS_LABEL_MAP = {
    "NORMAL": "正常",
    "ABNORMAL": "异常",
    "NOT_INSTALLED": "未安装",
    "JOINED": "已入域",
    "NOT_JOINED": "未入域",
    "NOT_APPLICABLE": "不适用",
}

# 异常工单状态
class ExceptionStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PENDING_SIGNOFF = "PENDING_SIGNOFF"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"

# 异常状态中文映射
EXCEPTION_STATUS_MAP = {
    "PENDING": "待分配",
    "PROCESSING": "处理中",
    "PENDING_SIGNOFF": "待签核",
    "CLOSED": "已结案",
    "REJECTED": "已驳回",
}
