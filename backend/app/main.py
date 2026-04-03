from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from .api.auth import auth as auth_router
from .api.data import data as data_router
from .api.ui import tasks as ui_tasks_router
from .api.ui import scenarios as ui_scenarios_router
from .api.ui import keywords as ui_keywords_router

settings = get_settings()

app = FastAPI(title="测试自动化平台", version="0.1.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "测试自动化平台 API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# 认证路由
app.include_router(auth_router.router, prefix="/api/v1")

# 项目相关的 API 路由
app.include_router(data_router.router, prefix="/api/v1")
app.include_router(ui_tasks_router.router, prefix="/api/v1")
app.include_router(ui_scenarios_router.router, prefix="/api/v1")
app.include_router(ui_keywords_router.router, prefix="/api/v1")