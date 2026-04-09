import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from .api.auth import auth as auth_router
from .api.data import data as data_router
from .api.ui import tasks as ui_tasks_router
from .api.ui import scenarios as ui_scenarios_router
from .api.ui import keywords as ui_keywords_router
from .api import agent
from .api import agent_management as agent_management_router
from .api import health as health_router
from .api import services as services_router
from .api import debug as debug_router
from .middleware import setup_rate_limit_middleware
from .middleware.performance import PerformanceMonitorMiddleware, get_performance_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

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

# 速率限制中间件
setup_rate_limit_middleware(app)

# 性能监控中间件
app.add_middleware(PerformanceMonitorMiddleware)


@app.get("/")
async def root():
    return {"message": "测试自动化平台 API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/v1/performance/stats")
async def get_performance_stats():
    """获取性能统计信息"""
    monitor = get_performance_monitor()
    if monitor:
        return monitor.get_stats()
    return {
        "message": "Performance monitoring not yet initialized"
    }


@app.websocket("/agent")
async def agent_websocket(websocket: WebSocket):
    """Agent WebSocket 连接端点"""
    await agent.websocket_endpoint(websocket)


# 认证路由
app.include_router(auth_router.router, prefix="/api/v1")

# 项目相关的 API 路由
app.include_router(data_router.router, prefix="/api/v1")
app.include_router(ui_tasks_router.router, prefix="/api/v1")
app.include_router(ui_scenarios_router.router, prefix="/api/v1")
app.include_router(ui_keywords_router.router, prefix="/api/v1")
app.include_router(agent_management_router.router, prefix="/api/v1")

# 健康检查路由
app.include_router(health_router.router, prefix="/api/v1", tags=["health"])

# 服务管理路由
app.include_router(services_router.router, prefix="/api/v1", tags=["services"])

# 调试文件路由
app.include_router(debug_router.router, prefix="/api/v1", tags=["debug"])