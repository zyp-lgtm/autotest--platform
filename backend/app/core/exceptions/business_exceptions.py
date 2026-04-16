"""
业务异常类

定义所有业务相关的异常
"""
from typing import Optional, Dict, Any


class BusinessException(Exception):
    """
    业务异常基类

    所有业务异常的父类，支持错误码和详细消息
    """

    def __init__(
        self,
        message: str,
        code: str = "BUSINESS_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400
    ):
        """
        初始化业务异常

        Args:
            message: 错误消息
            code: 错误码
            details: 详细信息
            status_code: HTTP 状态码
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class NotFoundException(BusinessException):
    """
    资源不存在异常

    当请求的资源不存在时抛出
    """

    def __init__(
        self,
        message: str,
        resource_type: str = "Resource",
        resource_id: Optional[str] = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            resource_type: 资源类型
            resource_id: 资源 ID
        """
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            code="NOT_FOUND",
            details=details,
            status_code=404
        )


class ValidationException(BusinessException):
    """
    参数验证失败异常

    当请求参数验证失败时抛出
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        errors: Optional[Dict[str, str]] = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            field: 错误字段名
            errors: 所有验证错误
        """
        details = {}
        if field:
            details["field"] = field
        if errors:
            details["errors"] = errors

        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=422
        )


class ExecutionException(BusinessException):
    """
    执行失败异常

    当任务或操作执行失败时抛出
    """

    def __init__(
        self,
        message: str,
        execution_id: Optional[str] = None,
        step_info: Optional[Dict[str, Any]] = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            execution_id: 执行 ID
            step_info: 步骤信息
        """
        details = {}
        if execution_id:
            details["execution_id"] = execution_id
        if step_info:
            details["step_info"] = step_info

        super().__init__(
            message=message,
            code="EXECUTION_ERROR",
            details=details,
            status_code=500
        )


class AuthenticationException(BusinessException):
    """
    认证失败异常

    当用户认证失败时抛出
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        reason: Optional[str] = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            reason: 失败原因
        """
        details = {}
        if reason:
            details["reason"] = reason

        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            details=details,
            status_code=401
        )


class PermissionDeniedException(BusinessException):
    """
    权限不足异常

    当用户权限不足时抛出
    """

    def __init__(
        self,
        message: str = "Permission denied",
        required_permission: Optional[str] = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            required_permission: 需要的权限
        """
        details = {}
        if required_permission:
            details["required_permission"] = required_permission

        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            details=details,
            status_code=403
        )


class ConflictException(BusinessException):
    """
    冲突异常

    当资源冲突时抛出（如重复创建）
    """

    def __init__(
        self,
        message: str,
        conflict_field: Optional[str] = None,
        conflict_value: Optional[str] = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            conflict_field: 冲突字段
            conflict_value: 冲突值
        """
        details = {}
        if conflict_field:
            details["conflict_field"] = conflict_field
        if conflict_value:
            details["conflict_value"] = conflict_value

        super().__init__(
            message=message,
            code="CONFLICT",
            details=details,
            status_code=409
        )


class RateLimitException(BusinessException):
    """
    速率限制异常

    当请求超过速率限制时抛出
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            retry_after: 重试等待时间（秒）
            limit: 速率限制
        """
        details = {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        if limit is not None:
            details["limit"] = limit

        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            details=details,
            status_code=429
        )
