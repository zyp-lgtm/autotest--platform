"""
结构化日志系统

提供统一的 JSON 格式日志输出和请求追踪
"""
import logging
import json
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
from pathlib import Path

# 请求 ID 上下文变量
REQUEST_ID_CTX: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
USER_ID_CTX: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    结构化日志格式化器

    将日志输出为 JSON 格式
    """

    def __init__(self, app_name: str = "test_platform"):
        super().__init__()
        self.app_name = app_name

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为 JSON

        Args:
            record: 日志记录

        Returns:
            JSON 字符串
        """
        # 基础日志数据
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "app": self.app_name,
        }

        # 添加上下文信息
        request_id = REQUEST_ID_CTX.get()
        if request_id:
            log_data["request_id"] = request_id

        user_id = USER_ID_CTX.get()
        if user_id:
            log_data["user_id"] = user_id

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }

        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # 添加位置信息（可选）
        if record.pathname and record.lineno:
            log_data["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName
            }

        return json.dumps(log_data, ensure_ascii=False)


class ContextualLogger(logging.LoggerAdapter):
    """
    上下文日志记录器

    自动添加请求 ID、用户 ID 等上下文信息
    """

    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        super().__init__(logger, extra or {})

    def process(self, msg: Any, kwargs: Dict[str, Any]) -> tuple:
        """
        处理日志消息，添加上下文信息

        Args:
            msg: 日志消息
            kwargs: 关键字参数

        Returns:
            处理后的消息和参数
        """
        # 添加额外字段
        extra = kwargs.get('extra', {})
        extra_fields = {}

        # 添加请求 ID
        request_id = REQUEST_ID_CTX.get()
        if request_id:
            extra_fields['request_id'] = request_id

        # 添加用户 ID
        user_id = USER_ID_CTX.get()
        if user_id:
            extra_fields['user_id'] = user_id

        # 添加自定义字段
        extra_fields.update(self.extra)
        extra_fields.update(extra)

        kwargs['extra'] = {'extra_fields': extra_fields}

        return msg, kwargs


def setup_logging(
    app_name: str = "test_platform",
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_output: bool = True
) -> None:
    """
    设置日志系统

    Args:
        app_name: 应用名称
        level: 日志级别
        log_file: 日志文件路径（可选）
        json_output: 是否输出 JSON 格式
    """
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 创建格式化器
    if json_output:
        formatter = StructuredFormatter(app_name)
    else:
        # 开发环境使用可读格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器（如果指定）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 配置第三方库日志级别
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)


def get_logger(name: str) -> ContextualLogger:
    """
    获取上下文日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        上下文日志记录器

    Example:
        logger = get_logger(__name__)
        logger.info("Processing request", extra={"order_id": "123"})
    """
    base_logger = logging.getLogger(name)
    return ContextualLogger(base_logger)


def log_request(
    method: str,
    path: str,
    status_code: int,
    duration: float,
    **kwargs
) -> None:
    """
    记录请求日志

    Args:
        method: HTTP 方法
        path: 请求路径
        status_code: 状态码
        duration: 请求时长（秒）
        **kwargs: 额外字段
    """
    logger = get_logger("app.request")
    logger.info(
        f"{method} {path} - {status_code}",
        extra={
            "http_method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": int(duration * 1000),
            **kwargs
        }
    )


def log_execution(
    task_id: str,
    execution_id: str,
    status: str,
    result: Optional[str] = None,
    duration: Optional[int] = None,
    **kwargs
) -> None:
    """
    记录任务执行日志

    Args:
        task_id: 任务 ID
        execution_id: 执行 ID
        status: 执行状态
        result: 执行结果
        duration: 执行时长（毫秒）
        **kwargs: 额外字段
    """
    logger = get_logger("app.execution")
    log_data = {
        "task_id": task_id,
        "execution_id": execution_id,
        "status": status,
    }

    if result:
        log_data["result"] = result
    if duration:
        log_data["duration_ms"] = duration

    log_data.update(kwargs)

    logger.info(f"Task execution: {status}", extra=log_data)


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "ERROR"
) -> None:
    """
    记录错误日志

    Args:
        error: 异常对象
        context: 错误上下文
        level: 日志级别
    """
    logger = get_logger("app.error")
    log_func = getattr(logger, level.lower())
    log_func(
        f"Error: {type(error).__name__}: {str(error)}",
        extra=context or {},
        exc_info=error
    )


# ============================================================================
# FastAPI 中间件集成
# ============================================================================

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件

    自动记录所有 HTTP 请求的日志
    """

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 生成请求 ID
        request_id = str(uuid.uuid4())
        REQUEST_ID_CTX.set(request_id)

        # 记录开始时间
        start_time = time.time()

        # 记录请求开始
        logger = get_logger("app.request")
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "http_method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None
            }
        )

        try:
            # 执行请求
            response = await call_next(request)

            # 计算时长
            duration = time.time() - start_time

            # 记录请求完成
            log_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration,
                request_id=request_id
            )

            # 添加请求 ID 到响应头
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration = time.time() - start_time

            # 记录请求失败
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "http_method": request.method,
                    "path": request.url.path,
                    "duration_ms": int(duration * 1000),
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=e
            )

            raise
        finally:
            # 清除上下文
            REQUEST_ID_CTX.set(None)
