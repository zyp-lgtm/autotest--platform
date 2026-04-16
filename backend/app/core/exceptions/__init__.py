"""
自定义异常类

定义系统中使用的所有业务异常
"""
from .business_exceptions import (
    BusinessException,
    NotFoundException,
    ValidationException,
    ExecutionException,
    AuthenticationException,
    PermissionDeniedException,
    ConflictException,
    RateLimitException
)
from .error_handler import (
    ErrorHandler,
    HTTPException,
    business_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
    error_handler,
    business_exception
)

__all__ = [
    # 异常类
    "BusinessException",
    "NotFoundException",
    "ValidationException",
    "ExecutionException",
    "AuthenticationException",
    "PermissionDeniedException",
    "ConflictException",
    "RateLimitException",
    # 处理器
    "ErrorHandler",
    "HTTPException",
    "error_handler",
    "business_exception_handler",
    "validation_exception_handler",
]
