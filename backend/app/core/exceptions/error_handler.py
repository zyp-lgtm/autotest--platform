"""
全局错误处理器

提供统一的异常处理和错误响应格式
"""
from typing import Dict, Any, Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging
import traceback

from .business_exceptions import BusinessException

logger = logging.getLogger(__name__)


class HTTPException(Exception):
    """
    HTTP 异常

    类似 FastAPI 的 HTTPException，但使用我们自己的格式
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        code: str = "HTTP_ERROR",
        details: Dict[str, Any] = None
    ):
        self.status_code = status_code
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class ErrorHandler:
    """
    错误处理器

    处理所有类型的异常并返回统一的响应格式
    """

    @staticmethod
    def handle_business_exception(exc: BusinessException) -> JSONResponse:
        """
        处理业务异常

        Args:
            exc: 业务异常

        Returns:
            JSON 响应
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )

    @staticmethod
    def handle_http_exception(exc: HTTPException) -> JSONResponse:
        """
        处理 HTTP 异常

        Args:
            exc: HTTP 异常

        Returns:
            JSON 响应
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )

    @staticmethod
    def handle_validation_exception(exc: Exception) -> JSONResponse:
        """
        处理参数验证异常（Pydantic）

        Args:
            exc: 验证异常

        Returns:
            JSON 响应
        """
        # 尝试解析 Pydantic 验证错误
        try:
            from pydantic import ValidationError
            if isinstance(exc, ValidationError):
                errors = {}
                for error in exc.errors():
                    field = ".".join(str(loc) for loc in error["loc"])
                    errors[field] = error["msg"]

                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "参数验证失败",
                            "details": {"errors": errors}
                        }
                    }
                )
        except ImportError:
            pass

        # 默认处理
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "参数验证失败",
                    "details": {"error": str(exc)}
                }
            }
        )

    @staticmethod
    def handle_generic_exception(exc: Exception) -> JSONResponse:
        """
        处理通用异常

        Args:
            exc: 异常

        Returns:
            JSON 响应
        """
        # 记录完整错误信息
        logger.error(f"未处理的异常: {type(exc).__name__}: {exc}")
        logger.error(traceback.format_exc())

        # 生产环境不返回详细错误信息
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "服务器内部错误",
                    "details": {}
                }
            }
        )


# ============================================================================
# FastAPI 异常处理器
# ============================================================================

async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """业务异常处理器"""
    return ErrorHandler.handle_business_exception(exc)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP 异常处理器"""
    return ErrorHandler.handle_http_exception(exc)


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """验证异常处理器"""
    return ErrorHandler.handle_validation_exception(exc)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    return ErrorHandler.handle_generic_exception(exc)


# ============================================================================
# 便捷函数
# ============================================================================

def error_handler(
    code: str,
    message: str,
    status_code: int = 400,
    details: Dict[str, Any] = None
) -> HTTPException:
    """
    创建 HTTP 异常

    Args:
        code: 错误码
        message: 错误消息
        status_code: HTTP 状态码
        details: 详细信息

    Returns:
        HTTP 异常
    """
    return HTTPException(
        status_code=status_code,
        message=message,
        code=code,
        details=details or {}
    )


def business_exception(
    message: str,
    code: str = "BUSINESS_ERROR",
    details: Dict[str, Any] = None,
    status_code: int = 400
) -> BusinessException:
    """
    创建业务异常

    Args:
        message: 错误消息
        code: 错误码
        details: 详细信息
        status_code: HTTP 状态码

    Returns:
        业务异常
    """
    return BusinessException(
        message=message,
        code=code,
        details=details,
        status_code=status_code
    )


def validation_exception(
    message: str,
    field: str = None,
    errors: Dict[str, str] = None
) -> Exception:
    """
    创建验证异常

    Args:
        message: 错误消息
        field: 错误字段
        errors: 所有错误

    Returns:
        验证异常
    """
    from .business_exceptions import ValidationException
    return ValidationException(message, field, errors)
