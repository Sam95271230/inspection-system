"""
统一响应格式
"""


def success(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}


def error(message="失败", code=400, data=None):
    return {"code": code, "message": message, "data": data}
