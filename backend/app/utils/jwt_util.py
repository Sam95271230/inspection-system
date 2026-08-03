"""
JWT 工具函数
"""

import os
import sys
from datetime import datetime, timedelta, timezone, timezone
from jose import jwt, JWTError

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# 安全检查：不允许使用默认弱密钥
if not JWT_SECRET or JWT_SECRET == "your-super-secret-jwt-key":
    print("[WARNING] JWT_SECRET 未设置或使用了默认弱密钥，请在 .env 中设置安全的 JWT_SECRET", file=sys.stderr)
    if not JWT_SECRET:
        JWT_SECRET = "CHANGE_ME_" + os.urandom(16).hex()
        print(f"[WARNING] 已生成临时随机密钥（重启后失效，请配置固定密钥）", file=sys.stderr)


def create_access_token(data: dict) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=JWT_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    """解析 JWT Token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except JWTError:
        return {}
