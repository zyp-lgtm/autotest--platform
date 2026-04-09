"""
简单内存缓存实现

提供带 TTL 的内存缓存功能，用于缓存频繁访问但不常变化的数据
"""
import time
import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SimpleCache:
    """
    简单的内存缓存实现

    特性：
    - 支持 TTL（过期时间）
    - 线程安全（使用 GIL）
    - 缓存统计
    - 自动清理过期项
    """

    def __init__(self, default_ttl: int = 300):
        """
        初始化缓存

        Args:
            default_ttl: 默认过期时间（秒），默认 5 分钟
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        if key not in self._cache:
            self.stats['misses'] += 1
            return None

        entry = self._cache[key]

        # 检查是否过期
        if entry['expires_at'] < time.time():
            # 过期，删除
            del self._cache[key]
            self.stats['evictions'] += 1
            self.stats['misses'] += 1
            return None

        self.stats['hits'] += 1
        return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 表示使用默认值
        """
        if ttl is None:
            ttl = self.default_ttl

        self._cache[key] = {
            'value': value,
            'created_at': time.time(),
            'expires_at': time.time() + ttl,
            'ttl': ttl
        }
        self.stats['sets'] += 1

    def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        if key in self._cache:
            del self._cache[key]
            self.stats['deletes'] += 1
            return True
        return False

    def clear(self) -> None:
        """清空所有缓存"""
        count = len(self._cache)
        self._cache.clear()
        self.stats['deletes'] += count

    def cleanup_expired(self) -> int:
        """
        清理过期项

        Returns:
            清理的项数
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry['expires_at'] < now
        ]

        for key in expired_keys:
            del self._cache[key]
            self.stats['evictions'] += 1

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total if total > 0 else 0

        return {
            **self.stats,
            'size': len(self._cache),
            'hit_rate': f"{hit_rate * 100:.1f}%"
        }

    def get_size(self) -> int:
        """获取缓存项数量"""
        return len(self._cache)


# 全局缓存实例
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """获取全局缓存实例"""
    return _cache


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    缓存装饰器

    Args:
        ttl: 过期时间（秒）
        key_prefix: 缓存键前缀

    Usage:
        @cached(ttl=60, key_prefix="user")
        async def get_user(user_id: str):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            # 生成缓存键
            cache_key = _generate_cache_key(
                func.__name__,
                key_prefix,
                args,
                kwargs
            )

            # 尝试从缓存获取
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 缓存未命中，执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            _cache.set(cache_key, result, ttl=ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # 生成缓存键
            cache_key = _generate_cache_key(
                func.__name__,
                key_prefix,
                args,
                kwargs
            )

            # 尝试从缓存获取
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 缓存未命中，执行函数
            result = func(*args, **kwargs)

            # 存入缓存
            _cache.set(cache_key, result, ttl=ttl)

            return result

        # 根据函数类型返回相应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def _generate_cache_key(
    func_name: str,
    prefix: str,
    args: tuple,
    kwargs: dict
) -> str:
    """
    生成缓存键

    Args:
        func_name: 函数名
        prefix: 键前缀
        args: 位置参数
        kwargs: 关键字参数

    Returns:
        缓存键
    """
    # 将参数转换为可哈希的字符串
    parts = []

    if prefix:
        parts.append(prefix)

    parts.append(func_name)

    # 处理位置参数（跳过 self 和 db session）
    for arg in args[2:]:  # 跳过 self 和 db
        if isinstance(arg, (str, int, float, bool)):
            parts.append(str(arg))
        elif arg is None:
            parts.append("None")

    # 处理关键字参数（排序以保证一致性）
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        if isinstance(v, (str, int, float, bool)):
            parts.append(f"{k}={v}")
        elif v is None:
            parts.append(f"{k}=None")

    key_string = ":".join(parts)

    # 如果键太长，使用哈希
    if len(key_string) > 200:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]
        return f"{prefix}:{func_name}:{key_hash}"

    return key_string


def cache_response(ttl: int = 300, key_func: Optional[Callable] = None):
    """
    FastAPI 响应缓存装饰器

    Args:
        ttl: 过期时间（秒）
        key_func: 自定义键生成函数

    Usage:
        @app.get("/api/v1/keywords")
        @cache_response(ttl=300)
        async def list_keywords():
            return {"keywords": [...]}
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(
                    func.__name__,
                    "",
                    args,
                    kwargs
                )

            # 尝试从缓存获取
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # 缓存未命中，执行函数
            result = await func(*args, **kwargs)
            logger.debug(f"Cache miss: {cache_key}")

            # 存入缓存
            _cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def invalidate_pattern(pattern: str) -> int:
    """
    使匹配模式的缓存失效

    Args:
        pattern: 键模式（支持通配符 *）

    Returns:
        失效的缓存项数量
    """
    import fnmatch

    keys_to_delete = [
        key for key in _cache._cache.keys()
        if fnmatch.fnmatch(key, pattern)
    ]

    for key in keys_to_delete:
        _cache.delete(key)

    return len(keys_to_delete)
