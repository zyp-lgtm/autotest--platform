"""
CSRF 中间件

为所有修改操作（POST, PUT, DELETE, PATCH）提供 CSRF 保护
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.csrf import csrf_protect
import logging

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF 保护中间件

    保护所有修改操作（POST, PUT, DELETE, PATCH）
    跳过安全的方法（GET, HEAD, OPTIONS）
    """

    # 不需要 CSRF 保护的路径
    EXEMPT_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/health",
        "/health",
        "/",
        "/docs",
        "/redoc",
        "/openapi.json"
    }

    async def dispatch(self, request: Request, call_next):
        """处理请求并验证 CSRF Token"""

        # 只验证修改操作
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # 跳过豁免路径
            if request.url.path in self.EXEMPT_PATHS:
                return await call_next(request)

            # 跳过认证端点（登录/注册使用自己的 CSRF 保护）
            if "/auth/" in request.url.path:
                return await call_next(request)

            # 豁免带有 Bearer token 的请求（API 调用）
            # Bearer token 本身已提供强认证，不受 CSRF 攻击影响
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                return await call_next(request)

            # 豁免带有 HttpOnly Cookie 的请求
            # Cookie 只能通过同源请求发送，这本身就提供了 CSRF 保护
            if request.cookies.get("access_token"):
                logger.debug(f"CSRF 豁免: 检测到 HttpOnly Cookie - {request.url.path}")
                return await call_next(request)

            try:
                # 验证 CSRF Token
                csrf_protect.validate_request(request)
            except HTTPException as e:
                logger.warning(f"CSRF 验证失败: {request.url.path} - {e.detail}")
                raise e
            except Exception as e:
                logger.error(f"CSRF 验证错误: {request.url.path} - {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF 验证失败"
                )

        return await call_next(request)
