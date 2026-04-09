"""
安全头中间件

添加安全相关的 HTTP 响应头
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全头中间件

    添加安全相关的 HTTP 响应头：
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - Content-Security-Policy: default-src 'self'
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 防止 MIME 类型嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 防止点击劫持
        response.headers["X-Frame-Options"] = "DENY"

        # 启用浏览器 XSS 保护
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS (仅 HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # 内容安全策略（基础版）
        response.headers[
            "Content-Security-Policy"
        ] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:"

        # Referrer 策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 权限策略
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response
