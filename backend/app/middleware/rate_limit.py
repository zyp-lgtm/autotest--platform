"""
API 速率限制中间件

防止 DDoS 攻击和暴力破解
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    内存中的速率限制器

    生产环境建议使用 Redis 实现分布式速率限制
    """

    def __init__(self):
        # 存储每个 IP 的请求记录 {ip: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        # 清理过期记录的间隔（秒）
        self.cleanup_interval = 60
        self.last_cleanup = time.time()

    def _cleanup_old_records(self, current_time: float):
        """清理过期的请求记录"""
        if current_time - self.last_cleanup > self.cleanup_interval:
            for ip in list(self.requests.keys()):
                # 只保留最近 60 秒的记录
                self.requests[ip] = [
                    (ts, count) for ts, count in self.requests[ip]
                    if current_time - ts < 60
                ]
                # 如果没有记录了，删除这个 IP
                if not self.requests[ip]:
                    del self.requests[ip]
            self.last_cleanup = current_time

    def is_allowed(
        self,
        ip: str,
        limit: int,
        window: int
    ) -> Tuple[bool, dict]:
        """
        检查是否允许请求

        Args:
            ip: 客户端 IP
            limit: 时间窗口内允许的请求数
            window: 时间窗口（秒）

        Returns:
            (是否允许, 限制信息)
        """
        current_time = time.time()
        self._cleanup_old_records(current_time)

        # 获取该 IP 的请求记录
        request_records = self.requests[ip]

        # 只看最近 window 秒的请求
        recent_requests = [
            ts for ts, _ in request_records
            if current_time - ts < window
        ]

        request_count = len(recent_requests)

        # 记录本次请求
        self.requests[ip].append((current_time, request_count + 1))

        # 检查是否超过限制
        if request_count >= limit:
            # 计算重置时间
            oldest_request = min(recent_requests) if recent_requests else current_time
            reset_time = int(oldest_request + window - current_time)

            return False, {
                "limit": limit,
                "remaining": 0,
                "reset": reset_time
            }

        return True, {
            "limit": limit,
            "remaining": limit - request_count - 1,
            "reset": window
        }


# 全局限速器实例
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件

    对不同的端点应用不同的速率限制策略
    """

    # 路径到限制规则的映射
    # 格式: (limit, window_seconds)
    RATE_LIMITS = {
        # 登录端点：严格限制
        "/api/v1/auth/login": (5, 60),  # 5 次/分钟
        "/api/v1/auth/register": (3, 60),  # 3 次/分钟

        # 执行端点：中等限制
        "/api/v1/tasks": (20, 60),  # 20 次/分钟
        "/api/v1/executions": (30, 60),  # 30 次/分钟

        # API 端点：宽松限制
        "/api/v1/keywords": (60, 60),  # 60 次/分钟
        "/api/v1/projects": (30, 60),  # 30 次/分钟

        # 默认限制
        "default": (60, 60)  # 60 次/分钟
    }

    # 白名单路径（不限制）
    WHITELIST = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/static",
    ]

    async def dispatch(self, request: Request, call_next):
        # 检查是否在白名单中
        path = request.url.path

        # 静态文件和文档不限制
        if any(path.startswith(whitelist_path) for whitelist_path in self.WHITELIST):
            return await call_next(request)

        # OPTIONS 请求不限制（预检）
        if request.method == "OPTIONS":
            return await call_next(request)

        # 获取客户端 IP
        ip = self._get_client_ip(request)

        # 获取该路径的速率限制规则
        limit_rule = self._get_limit_rule(path)

        # 检查是否允许请求
        allowed, info = rate_limiter.is_allowed(ip, limit_rule[0], limit_rule[1])

        # 添加速率限制头到响应
        response = await call_next(request)

        # 如果使用了自定义响应对象
        if hasattr(response, 'headers'):
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(info["reset"])

        if not allowed:
            logger.warning(f"速率限制触发: IP={ip}, Path={path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "retry_after": info["reset"]
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["reset"])
                }
            )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实 IP"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 回退到直接连接的 IP
        if request.client:
            return request.client.host

        return "unknown"

    def _get_limit_rule(self, path: str) -> Tuple[int, int]:
        """获取路径对应的限制规则"""
        # 精确匹配
        if path in self.RATE_LIMITS:
            return self.RATE_LIMITS[path]

        # 前缀匹配
        for rate_path, rule in self.RATE_LIMITS.items():
            if rate_path != "default" and path.startswith(rate_path):
                return rule

        # 默认限制
        return self.RATE_LIMITS["default"]


def setup_rate_limit_middleware(app):
    """
    设置速率限制中间件到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    app.add_middleware(RateLimitMiddleware)
    logger.info("✓ 速率限制中间件已启用")
