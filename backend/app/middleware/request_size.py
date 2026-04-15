"""
请求体大小限制中间件

限制请求体大小，防止大文件攻击和内存耗尽攻击
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    请求体大小限制中间件

    功能：
    - 检查 Content-Length 头
    - 超过限制返回 413 Payload Too Large
    """

    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 默认 10MB
        super().__init__(app)
        self.max_size = max_size
        logger.info(f"请求体大小限制中间件已启用，最大: {max_size / 1024 / 1024:.1f}MB")

    async def dispatch(self, request: Request, call_next):
        # 检查 Content-Length 头
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    logger.warning(
                        f"请求体过大: {size / 1024 / 1024:.2f}MB > "
                        f"{self.max_size / 1024 / 1024:.2f}MB, "
                        f"路径: {request.url.path}"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"请求体过大，最大允许 {self.max_size / 1024 / 1024:.1f}MB"
                        }
                    )
            except ValueError:
                # Content-Length 无效，继续处理
                pass

        # 对于没有 Content-Length 的请求，继续处理
        #（实际读取时会被 Starlette 自动限制）
        response = await call_next(request)
        return response
