from minio import Minio
from minio.error import S3Error
import os
import io
import json
from datetime import timedelta

def get_minio_client():
    return Minio(
        os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
        secure=False,
    )


def set_bucket_public_policy(client, bucket_name):
    """
    设置 bucket 为公开可读
    """
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
            }
        ]
    }
    try:
        client.set_bucket_policy(bucket_name, json.dumps(policy))
        print(f"Bucket '{bucket_name}' 已设置为公开可读")
    except S3Error as e:
        print(f"设置 bucket policy 失败: {e}")


def ensure_bucket_exists():
    client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET", "inspection-images")
    
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            set_bucket_public_policy(client, bucket_name)
            print(f"Bucket '{bucket_name}' 创建成功")
        else:
            print(f"Bucket '{bucket_name}' 已存在")
            set_bucket_public_policy(client, bucket_name)
    except Exception as e:
        print(f"MinIO 连接失败: {e}")


def upload_file(object_name: str, file_data: bytes, content_type: str = "image/jpeg") -> str:
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
    
    # 返回公开访问 URL
    external_minio_url = os.getenv("MINIO_EXTERNAL_URL", "http://localhost:9000")
    return f"{external_minio_url}/{bucket_name}/{object_name}"
