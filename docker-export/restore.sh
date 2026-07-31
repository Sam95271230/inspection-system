#!/bin/bash
set -e

echo "=========================================="
echo "开始恢复产线电脑巡检系统"
echo "=========================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误：未安装 Docker"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "错误：未安装 Docker Compose"
    exit 1
fi

# 1. 加载 Docker 镜像
echo "1. 加载 Docker 镜像..."
docker load -i images.tar

# 2. 启动基础服务
echo "2. 启动 PostgreSQL 和 MinIO..."
docker compose up -d postgres minio

# 3. 等待服务启动
echo "3. 等待服务启动..."
sleep 15

# 4. 恢复数据库
echo "4. 恢复数据库..."
docker cp backup/inspection_db.sql inspection_postgres:/tmp/
docker exec inspection_postgres psql -U inspection_user -d inspection_db -f /tmp/inspection_db.sql

# 5. 恢复 MinIO 数据
echo "5. 恢复 MinIO 数据..."
docker cp backup/minio_data/. inspection_minio:/data/

# 6. 启动所有服务
echo "6. 启动所有服务..."
docker compose up -d

echo "=========================================="
echo "恢复完成！"
echo "前端访问：http://localhost:8081"
echo "后端 API：http://localhost:8080"
echo "MinIO 控制台：http://localhost:9001"
echo "=========================================="
