import logging
import os
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from .core.config import get_settings
from .core.exceptions import (
    business_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
    HTTPException
)
from .core.exceptions.business_exceptions import BusinessException
from .api.auth import auth as auth_router
from .api.data import data as data_router
from .api.projects import router as projects_router
from .api.ui import tasks as ui_tasks_router
from .api.ui import scenarios as ui_scenarios_router
from .api.ui import keywords as ui_keywords_router
from .api import agent
from .api import agent_management as agent_management_router
from .api import health as health_router
from .api import services as services_router
from .api import debug as debug_router
from .api import cache as cache_router
from .api import audit as audit_router
# 暂时移除所有新增API路由以解决映射问题
# from .api import environments as environments_router
# from .api import test_data as test_data_router
# from .api import batch as batch_router
# from .api import scheduled_jobs as scheduled_jobs_router
from .middleware import setup_rate_limit_middleware
from .middleware.performance import PerformanceMonitorMiddleware, get_performance_monitor
from .middleware.security import SecurityHeadersMiddleware
from .middleware.csrf import CSRFMiddleware
from .middleware.request_size import RequestSizeLimitMiddleware
from .middleware.audit import AuditMiddleware

# ============================================================================
# 配置结构化日志系统
# ============================================================================
from .core.logging import setup_logging, get_logger, RequestLoggingMiddleware

# 设置日志系统
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE", None)  # 可选：日志文件路径
json_output = os.getenv("ENV", "development") != "development"  # 生产环境使用 JSON

setup_logging(
    app_name="test_platform",
    level=log_level,
    log_file=log_file,
    json_output=json_output
)

# 获取根日志记录器
logger = get_logger(__name__)

settings = get_settings()

app = FastAPI(title="测试自动化平台", version="0.1.0", redirect_slashes=False)

# ============================================================================
# 全局异常处理器
# ============================================================================

# 业务异常处理器
app.add_exception_handler(BusinessException, business_exception_handler)

# HTTP 异常处理器
app.add_exception_handler(HTTPException, http_exception_handler)

# 参数验证异常处理器（Pydantic）
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 通用异常处理器（捕获所有未处理的异常）
app.add_exception_handler(Exception, generic_exception_handler)

# 创建并配置静态文件目录
screenshots_dir = Path("screenshots")
screenshots_dir.mkdir(exist_ok=True)

# 挂载静态文件服务
app.mount("/screenshots", StaticFiles(directory=str(screenshots_dir)), name="screenshots")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSRF 保护中间件（在 CORS 之后）
app.add_middleware(CSRFMiddleware)

# 安全头中间件
app.add_middleware(SecurityHeadersMiddleware)

# 请求体大小限制中间件
app.add_middleware(RequestSizeLimitMiddleware, max_size=settings.MAX_REQUEST_SIZE)

# 速率限制中间件
setup_rate_limit_middleware(app)

# 性能监控中间件
app.add_middleware(PerformanceMonitorMiddleware)

# 审计日志中间件
app.add_middleware(AuditMiddleware)

# 请求日志中间件（最外层，记录所有请求）
app.add_middleware(RequestLoggingMiddleware)


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
app.include_router(projects_router, prefix="/api/v1")
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

# 缓存管理路由
app.include_router(cache_router.router, prefix="/api/v1", tags=["cache"])

# 审计日志路由
app.include_router(audit_router.router, prefix="/api/v1")

# Phase 2 & 3 新增路由 - 重新启用
from .api import environments as environments_router
from .api import test_data as test_data_router
from .api import batch as batch_router
from .api import scheduled_jobs as scheduled_jobs_router
from .api import recording as recording_router

app.include_router(environments_router.router, prefix="/api/v1")
app.include_router(test_data_router.router, prefix="/api/v1")
app.include_router(batch_router.router, prefix="/api/v1")
app.include_router(scheduled_jobs_router.router, prefix="/api/v1")
app.include_router(recording_router.router, prefix="/api/v1")


# ============================================================================
# 应用启动事件
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("测试自动化平台启动中...")
    logger.info("=" * 60)

    # 1. 数据库健康检查和自动初始化
    logger.info("检查数据库状态...")
    from .core.database_health import ensure_database_ready

    if not ensure_database_ready():
        logger.error("✗ 数据库初始化失败，应用可能无法正常工作")
        logger.error("请手动运行: python3 init_db.py")
    else:
        logger.info("✓ 数据库就绪")

    # 2. 缓存预热
    try:
        from .utils.cache_warmup import warmup_cache
        logger.info("预热缓存...")
        await warmup_cache()
        logger.info("✓ 缓存预热完成")
    except Exception as e:
        logger.warning(f"缓存预热失败（非致命）: {e}")

    logger.info("=" * 60)
    logger.info("✓ 测试自动化平台启动完成")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger = get_logger(__name__)
    logger.info("测试自动化平台关闭中...")

    # 清理资源
    # TODO: 关闭数据库连接、清理缓存等

    logger.info("✓ 测试自动化平台已关闭")