from minio import Minio
from minio.error import S3Error
import os
import io
from datetime import timedelta

# 模块级 MinIO 客户端单例
_minio_client = None


def get_minio_client() -> Minio:
    """获取 MinIO 客户端单例（延迟初始化 + 复用连接）"""
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
            secure=False,
        )
    return _minio_client


def ensure_bucket_exists():
    """确保 bucket 存在（不设置公开读策略，改用预签名 URL）"""
    client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET", "inspection-images")

    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' 创建成功")
        else:
            print(f"Bucket '{bucket_name}' 已存在")
    except Exception as e:
        print(f"MinIO 连接失败: {e}")


def upload_file(object_name: str, file_data: bytes, content_type: str = "image/jpeg") -> str:
    """上传文件到 MinIO，返回 storage_key"""
    client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET", "inspection-images")

    data_stream = io.BytesIO(file_data)

    client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=data_stream,
        length=len(file_data),
        content_type=content_type,
    )

    return object_name


def get_presigned_url(storage_key: str, expires_hours: int = 24) -> str:
    """生成预签名 URL"""
    if not storage_key:
        return ""
    client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET", "inspection-images")
    try:
        return client.presigned_get_object(bucket_name, storage_key, expires=timedelta(hours=expires_hours))
    except Exception:
        external_url = os.getenv("MINIO_EXTERNAL_URL", "http://localhost:9000")
        return f"{external_url}/{bucket_name}/{storage_key}"


def get_image_url(storage_key: str) -> str:
    """获取图片 URL（预签名，1小时有效，适合 Web 展示）"""
    return get_presigned_url(storage_key, expires_hours=1)


def get_email_image_url(storage_key: str) -> str:
    """获取邮件用图片 URL（预签名，7天有效）"""
    return get_presigned_url(storage_key, expires_hours=168)
