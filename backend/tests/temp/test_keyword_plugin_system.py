"""
关键字插件系统测试

演示如何使用插件化关键字系统。
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.services.keywords.keyword_registry import (
    keyword_registry,
    register_ui_keyword,
    register_api_keyword,
    register_custom_keyword
)
from app.services.keywords.example_plugin import load_example_keywords
from app.services.keyword_engine import KeywordEngine


# ============================================================================
# 测试插件注册和执行
# ============================================================================

class TestKeywordPluginSystem:
    """插件系统测试"""

    def test_register_custom_keyword(self):
        """测试注册自定义关键字"""
        # 定义测试关键字
        async def test_keyword(parameters, context):
            return {"success": True, "data": {"result": "ok"}}

        # 注册关键字
        keyword_registry.register_handler(
            category="test",
            name="TEST_KEYWORD",
            handler=test_keyword,
            description="测试关键字",
            author="Test",
            version="1.0.0"
        )

        # 验证注册
        assert keyword_registry.exists("test", "TEST_KEYWORD")

        # 获取信息
        info = keyword_registry.get_keyword_info("test", "TEST_KEYWORD")
        assert info is not None
        assert info["name"] == "TEST_KEYWORD"
        assert info["category"] == "test"
        assert info["author"] == "Test"

    @pytest.mark.asyncio
    async def test_execute_custom_keyword(self):
        """测试执行自定义关键字"""
        # 定义测试关键字
        async def test_keyword(parameters, context):
            name = parameters.get("name", "world")
            return {"success": True, "data": {"message": f"Hello, {name}"}}

        # 注册关键字
        keyword_registry.register_handler(
            category="test",
            name="GREET",
            handler=test_keyword
        )

        # 执行关键字
        result = await keyword_registry.execute(
            category="test",
            name="GREET",
            parameters={"name": "Claude"},
            context={}
        )

        # 验证结果
        assert result["success"] is True
        assert result["data"]["message"] == "Hello, Claude"

    def test_decorator_registration(self):
        """测试装饰器注册"""
        # 使用装饰器注册
        @register_ui_keyword(
            name="TEST_CLICK",
            description="测试点击"
        )
        async def test_click(parameters, context):
            return {"success": True}

        # 验证注册
        assert keyword_registry.exists("ui", "TEST_CLICK")

    @pytest.mark.asyncio
    async def test_alias_support(self):
        """测试别名功能"""
        # 定义带别名的关键字
        async def test_keyword(parameters, context):
            return {"success": True}

        # 使用别名注册
        keyword_registry.register_handler(
            category="test",
            name="LONG_NAME_KEYWORD",
            handler=test_keyword
        )

        # 设置别名
        keyword_registry._aliases["SHORT"] = ("test", "LONG_NAME_KEYWORD")

        # 通过别名执行
        result = await keyword_registry.execute(
            category="test",
            name="SHORT",
            parameters={},
            context={}
        )

        assert result["success"] is True

    def test_list_keywords(self):
        """测试列出关键字"""
        # 注册几个测试关键字
        for i in range(3):
            async def test_keyword(params, ctx, i=i):
                return {"success": True}

            keyword_registry.register_handler(
                category="test",
                name=f"KEYWORD_{i}",
                handler=test_keyword
            )

        # 列出所有测试关键字
        keywords = keyword_registry.list_keywords("test")

        assert len(keywords) >= 3
        keyword_names = [k["name"] for k in keywords]
        assert "KEYWORD_0" in keyword_names
        assert "KEYWORD_1" in keyword_names
        assert "KEYWORD_2" in keyword_names

    def test_unregister_keyword(self):
        """测试注销关键字"""
        # 注册关键字
        async def test_keyword(params, ctx):
            return {"success": True}

        keyword_registry.register_handler(
            category="test",
            name="TEMP_KEYWORD",
            handler=test_keyword
        )

        assert keyword_registry.exists("test", "TEMP_KEYWORD")

        # 注销关键字
        success = keyword_registry.unregister("test", "TEMP_KEYWORD")
        assert success is True
        assert not keyword_registry.exists("test", "TEMP_KEYWORD")

    @pytest.mark.asyncio
    async def test_keyword_error_handling(self):
        """测试关键字错误处理"""
        # 定义会抛出异常的关键字
        async def failing_keyword(parameters, context):
            raise ValueError("测试错误")

        keyword_registry.register_handler(
            category="test",
            name="FAILING",
            handler=failing_keyword
        )

        # 执行失败的关键字
        result = await keyword_registry.execute(
            category="test",
            name="FAILING",
            parameters={},
            context={}
        )

        # 验证错误被正确处理
        assert result["success"] is False
        assert "error" in result


# ============================================================================
# 测试 KeywordEngine 集成
# ============================================================================

class TestKeywordEngineIntegration:
    """KeywordEngine 集成测试"""

    @pytest.mark.asyncio
    async def test_engine_with_registry(self):
        """测试引擎使用注册表"""
        # 注册测试关键字
        async def test_keyword(parameters, context):
            value = parameters.get("value")
            return {"success": True, "data": {"value": value}}

        keyword_registry.register_handler(
            category="custom",
            name="TEST",
            handler=test_keyword
        )

        # 创建使用注册表的引擎
        engine = KeywordEngine(use_registry=True)

        # 执行关键字
        result = await engine.execute(
            keyword_def={"name": "TEST", "category": "custom"},
            parameters={"value": "test_value"},
            context={}
        )

        # 验证结果
        assert result["success"] is True
        assert result["data"]["value"] == "test_value"

    @pytest.mark.asyncio
    async def test_engine_register_method(self):
        """测试引擎的注册方法"""
        engine = KeywordEngine(use_registry=True)

        # 使用引擎方法注册
        engine.register_keyword(
            category="custom",
            name="ENGINE_TEST",
            handler=lambda params, ctx: {"success": True},
            description="通过引擎注册"
        )

        # 验证注册
        assert engine.get_keyword_info("custom", "ENGINE_TEST") is not None

    @pytest.mark.asyncio
    async def test_engine_list_keywords(self):
        """测试引擎列出关键字"""
        engine = KeywordEngine(use_registry=True)

        # 注册几个关键字
        for i in range(3):
            engine.register_keyword(
                category="custom",
                name=f"KEY_{i}",
                handler=lambda params, ctx: {"success": True}
            )

        # 列出关键字
        keywords = engine.list_keywords("custom")

        assert len(keywords) >= 3


# ============================================================================
# 测试示例插件
# ============================================================================

class TestExamplePlugin:
    """示例插件测试"""

    @pytest.mark.asyncio
    async def test_custom_navigate(self):
        """测试自定义导航关键字"""
        # Mock page 对象
        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.title = AsyncMock(return_value="Test Page")

        # 执行导航
        result = await keyword_registry.execute(
            category="ui",
            name="CUSTOM_NAVIGATE",
            parameters={"url": "https://example.com"},
            context={"page": mock_page}
        )

        # 验证
        assert result["success"] is True
        mock_page.goto.assert_called_once()

    @pytest.mark.asyncio
    async def test_data_transform(self):
        """测试数据转换关键字"""
        # Base64 编码
        result = await keyword_registry.execute(
            category="custom",
            name="DATA_TRANSFORM",
            parameters={
                "operation": "base64_encode",
                "data": "hello"
            },
            context={}
        )

        assert result["success"] is True
        assert result["data"]["result"] == "aGVsbG8="

    @pytest.mark.asyncio
    async def test_assert_custom(self):
        """测试自定义断言"""
        # 相等断言
        result = await keyword_registry.execute(
            category="custom",
            name="ASSERT_CUSTOM",
            parameters={
                "type": "equals",
                "actual": "hello",
                "expected": "hello"
            },
            context={}
        )

        assert result["success"] is True
        assert result["data"]["passed"] is True

        # 不相等断言
        result = await keyword_registry.execute(
            category="custom",
            name="ASSERT_CUSTOM",
            parameters={
                "type": "equals",
                "actual": "hello",
                "expected": "world"
            },
            context={}
        )

        assert result["success"] is False
        assert "error" in result


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])


# ============================================================================
# 使用示例
# ============================================================================

async def demonstrate_plugin_usage():
    """演示插件使用方式"""

    print("=" * 60)
    print("关键字插件系统演示")
    print("=" * 60)

    # 1. 注册自定义关键字
    print("\n1. 注册自定义关键字...")

    @register_ui_keyword(name="MY_CLICK", description="我的点击")
    async def my_click(parameters, context):
        selector = parameters.get("selector")
        print(f"   点击元素: {selector}")
        return {"success": True, "data": {"clicked": True}}

    print("   ✅ 关键字 MY_CLICK 已注册")

    # 2. 执行关键字
    print("\n2. 执行关键字...")
    result = await keyword_registry.execute(
        category="ui",
        name="MY_CLICK",
        parameters={"selector": "#button"},
        context={}
    )
    print(f"   结果: {result}")

    # 3. 列出所有关键字
    print("\n3. 列出所有 UI 关键字...")
    ui_keywords = keyword_registry.list_keywords("ui")
    print(f"   总数: {len(ui_keywords)}")
    for kw in ui_keywords[:5]:  # 只显示前5个
        print(f"   - {kw['name']}: {kw.get('description', '')}")

    # 4. 使用 KeywordEngine
    print("\n4. 使用 KeywordEngine...")
    engine = KeywordEngine(use_registry=True)

    engine.register_keyword(
        category="custom",
        name="ENGINE_TEST",
        handler=lambda p, c: {"success": True, "test": True},
        description="引擎测试"
    )

    result = await engine.execute(
        keyword_def={"name": "ENGINE_TEST", "category": "custom"},
        parameters={},
        context={}
    )
    print(f"   结果: {result}")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demonstrate_plugin_usage())
