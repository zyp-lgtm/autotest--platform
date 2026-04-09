"""
缓存系统单元测试
"""
import pytest
import time
from app.utils.cache import SimpleCache, cached, invalidate_pattern


class TestSimpleCache:
    """SimpleCache 类测试"""

    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        cache = SimpleCache()

        # 设置缓存
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # 设置不同类型的值
        cache.set("key2", 123)
        assert cache.get("key2") == 123

        cache.set("key3", {"nested": "dict"})
        assert cache.get("key3") == {"nested": "dict"}

    def test_cache_get_non_existent(self):
        """测试获取不存在的键"""
        cache = SimpleCache()
        assert cache.get("non_existent") is None

    def test_cache_expiration(self):
        """测试缓存过期"""
        cache = SimpleCache(default_ttl=1)  # 1 秒过期

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # 等待过期
        time.sleep(1.5)
        assert cache.get("key1") is None

    def test_cache_custom_ttl(self):
        """测试自定义 TTL"""
        cache = SimpleCache(default_ttl=10)

        # 设置 1 秒过期的缓存
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"

        # 等待过期
        time.sleep(1.5)
        assert cache.get("key1") is None

        # 默认 TTL 的缓存应该还在
        cache.set("key2", "value2")
        time.sleep(1.5)
        assert cache.get("key2") == "value2"

    def test_cache_delete(self):
        """测试删除缓存"""
        cache = SimpleCache()

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # 删除缓存
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

        # 删除不存在的键
        assert cache.delete("non_existent") is False

    def test_cache_clear(self):
        """测试清空缓存"""
        cache = SimpleCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert cache.get_size() == 3

        cache.clear()

        assert cache.get_size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

    def test_cache_cleanup_expired(self):
        """测试清理过期缓存"""
        cache = SimpleCache(default_ttl=1)

        cache.set("key1", "value1")
        cache.set("key2", "value2", ttl=2)
        cache.set("key3", "value3", ttl=1)

        assert cache.get_size() == 3

        # 等待 key1 和 key3 过期
        time.sleep(1.5)

        # 清理过期项
        count = cache.cleanup_expired()

        assert count == 2
        assert cache.get_size() == 1
        assert cache.get("key2") == "value2"

    def test_cache_stats(self):
        """测试缓存统计"""
        cache = SimpleCache()

        # 初始统计
        stats = cache.get_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['sets'] == 0
        assert stats['size'] == 0

        # 设置缓存
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # 命中
        cache.get("key1")
        cache.get("key2")

        # 未命中
        cache.get("non_existent")

        stats = cache.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['sets'] == 2
        assert stats['size'] == 2

    def test_cache_hit_rate(self):
        """测试缓存命中率"""
        cache = SimpleCache()

        cache.set("key1", "value1")

        # 2 次命中，1 次未命中
        cache.get("key1")
        cache.get("key1")
        cache.get("non_existent")

        stats = cache.get_stats()
        assert stats['hit_rate'] == "66.7%"  # 2/3

    def test_cache_decorator(self):
        """测试缓存装饰器"""
        cache = SimpleCache()

        call_count = 0

        @cached(ttl=10)
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # 第一次调用，执行函数
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # 第二次调用，使用缓存
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # 没有增加

        # 不同参数，执行函数
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2

    def test_invalidate_pattern(self):
        """测试模式失效"""
        cache = SimpleCache()

        cache.set("user:1:name", "Alice")
        cache.set("user:1:email", "alice@example.com")
        cache.set("user:2:name", "Bob")
        cache.set("product:1:name", "Laptop")

        assert cache.get_size() == 4

        # 使所有 user:* 缓存失效
        count = invalidate_pattern("user:*")

        assert count == 3
        assert cache.get_size() == 1
        assert cache.get("product:1:name") == "Laptop"
        assert cache.get("user:1:name") is None


@pytest.mark.asyncio
class TestAsyncCache:
    """异步缓存测试"""

    async def test_cached_async_function(self):
        """测试异步函数缓存"""
        cache = SimpleCache()

        call_count = 0

        @cached(ttl=10)
        async def async_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # 模拟异步操作
            return x * 3

        import asyncio

        # 第一次调用
        result1 = await async_function(5)
        assert result1 == 15
        assert call_count == 1

        # 第二次调用，使用缓存
        result2 = await async_function(5)
        assert result2 == 15
        assert call_count == 1

    async def test_cache_with_async_db_query(self):
        """测试缓存异步数据库查询"""
        cache = SimpleCache()

        query_count = 0

        async def mock_db_query(user_id: str):
            nonlocal query_count
            query_count += 1
            await asyncio.sleep(0.01)
            return {"id": user_id, "name": f"User {user_id}"}

        # 包装缓存
        @cached(ttl=60, key_prefix="user")
        async def get_user(user_id: str):
            return await mock_db_query(user_id)

        import asyncio

        # 第一次查询
        user1 = await get_user("123")
        assert user1["name"] == "User 123"
        assert query_count == 1

        # 第二次查询，使用缓存
        user2 = await get_user("123")
        assert user2["name"] == "User 123"
        assert query_count == 1  # 没有增加

        # 不同用户，执行查询
        user3 = await get_user("456")
        assert user3["name"] == "User 456"
        assert query_count == 2
