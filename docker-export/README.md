# 产线电脑巡检系统 - Docker 环境包

## 包含内容

- `backend/`：FastAPI 后端代码
- `frontend/`：Vue3 前端代码
- `docker-compose.yml`：容器编排
- `images.tar`：Docker 镜像
- `backup/inspection_db.sql`：PostgreSQL 数据备份
- `backup/minio_data/`：MinIO 文件备份
- `restore.sh`：一键恢复脚本

## 快速恢复

```bash
cd docker-export
./restore.sh

