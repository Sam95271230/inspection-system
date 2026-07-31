from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.utils.minio_client import ensure_bucket_exists
from app.routers import auth, plant_dict, inspection, user, role, exception, email_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_bucket_exists()
    yield


app = FastAPI(
    title="产线电脑巡检系统",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(plant_dict.router, prefix="/api/v1")
app.include_router(inspection.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(role.router, prefix="/api/v1")
app.include_router(exception.router, prefix="/api/v1")
app.include_router(email_config.router, prefix="/api/v1")

@app.get("/api/v1/health")
def health_check():
    return {"code": 200, "message": "服务运行中", "data": None}
