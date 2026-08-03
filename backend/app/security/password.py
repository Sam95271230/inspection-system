"""
密码加密工具，直接使用 bcrypt 库
"""

import bcrypt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password
    )


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    # bcrypt 密码最长 72 字节，这里做截断
    password_bytes = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")
