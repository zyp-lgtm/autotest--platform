"""
性能监控中间件

记录 API 请求的处理时间，识别慢查询和性能瓶颈
"""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable

logger = logging.getLogger(__name__)

# 全局性能监控实例
_performance_monitor: 'PerformanceMonitorMiddleware' = None


def get_performance_monitor():
    """获取全局性能监控实例"""
    return _performance_monitor


# 性能阈值（毫秒）
SLOW_REQUEST_THRESHOLD = 1000  # 慢请求阈值：1秒
VERY_SLOW_REQUEST_THRESHOLD = 3000  # 极慢请求阈值：3秒


class PerformanceMonitorMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件

    功能：
    1. 记录每个请求的处理时间
    2. 识别慢查询（>1秒）
    3. 记录极慢请求（>3秒）为警告
    4. 定期输出性能统计信息
    """

    def __init__(self, app, slow_threshold: int = SLOW_REQUEST_THRESHOLD):
        super().__init__(app)
        self.slow_threshold = slow_threshold
        self.request_stats = {
            'total': 0,
            'slow': 0,
            'very_slow': 0,
            'paths': {}
        }

        # 设置全局实例
        global _performance_monitor
        _performance_monitor = self

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录性能数据"""

        # 跳过健康检查和监控端点
        if request.url.path in ['/health', '/api/v1/health', '/metrics']:
            return await call_next(request)

        # 记录开始时间
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算处理时间（毫秒）
        process_time = (time.time() - start_time) * 1000

        # 更新统计信息
        self._update_stats(request.url.path, process_time)

        # 添加响应头
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        # 记录性能日志
        self._log_performance(request, process_time)

        return response

    def _update_stats(self, path: str, process_time: float):
        """更新性能统计信息"""
        self.request_stats['total'] += 1

        # 按路径统计
        if path not in self.request_stats['paths']:
            self.request_stats['paths'][path] = {
                'count': 0,
                'total_time': 0,
                'max_time': 0,
                'slow_count': 0
            }

        stats = self.request_stats['paths'][path]
        stats['count'] += 1
        stats['total_time'] += process_time
        stats['max_time'] = max(stats['max_time'], process_time)

        if process_time >= VERY_SLOW_REQUEST_THRESHOLD:
            self.request_stats['very_slow'] += 1
            stats['slow_count'] += 1
        elif process_time >= self.slow_threshold:
            self.request_stats['slow'] += 1
            stats['slow_count'] += 1

    def _log_performance(self, request: Request, process_time: float):
        """记录性能日志"""

        # 极慢请求：警告级别
        if process_time >= VERY_SLOW_REQUEST_THRESHOLD:
            logger.warning(
                f"🐌 极慢请求: {request.method} {request.url.path} "
                f"耗时 {process_time:.0f}ms"
            )

        # 慢请求：信息级别
        elif process_time >= self.slow_threshold:
            logger.info(
                f"⚠️  慢请求: {request.method} {request.url.path} "
                f"耗时 {process_time:.0f}ms"
            )

        # 正常请求：调试级别（每100个请求输出一次统计）
        elif self.request_stats['total'] % 100 == 0:
            self._log_stats()

    def _log_stats(self):
        """输出性能统计信息"""
        total = self.request_stats['total']
        slow = self.request_stats['slow']
        very_slow = self.request_stats['very_slow']

        if total == 0:
            return

        slow_pct = (slow + very_slow) / total * 100

        logger.info(
            f"📊 性能统计: 总请求 {total}, "
            f"慢请求 {slow + very_slow} ({slow_pct:.1f}%), "
            f"平均响应时间 {self._get_avg_response_time():.0f}ms"
        )

        # 输出最慢的路径
        slow_paths = sorted(
            self.request_stats['paths'].items(),
            key=lambda x: x[1]['max_time'],
            reverse=True
        )[:5]

        if slow_paths:
            logger.info("🐌 最慢的路径:")
            for path, stats in slow_paths:
                avg_time = stats['total_time'] / stats['count']
                logger.info(
                    f"  - {path}: "
                    f"平均 {avg_time:.0f}ms, "
                    f"最大 {stats['max_time']:.0f}ms, "
                    f"慢请求 {stats['slow_count']}/{stats['count']}"
                )

    def _get_avg_response_time(self) -> float:
        """计算平均响应时间"""
        total_time = sum(
            s['total_time'] for s in self.request_stats['paths'].values()
        )
        total_count = sum(
            s['count'] for s in self.request_stats['paths'].values()
        )
        return total_time / total_count if total_count > 0 else 0

    def get_stats(self) -> dict:
        """获取性能统计信息"""
        return {
            'total_requests': self.request_stats['total'],
            'slow_requests': self.request_stats['slow'],
            'very_slow_requests': self.request_stats['very_slow'],
            'avg_response_time_ms': self._get_avg_response_time(),
            'paths': {
                path: {
                    'count': stats['count'],
                    'avg_time_ms': stats['total_time'] / stats['count'],
                    'max_time_ms': stats['max_time'],
                    'slow_count': stats['slow_count']
                }
                for path, stats in self.request_stats['paths'].items()
            }
        }
