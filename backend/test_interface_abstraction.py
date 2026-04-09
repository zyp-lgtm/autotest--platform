"""
接口抽象单元测试示例

演示如何使用 Protocol 接口进行单元测试，
验证依赖注入和接口抽象的正确性。
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any

# 导入接口
from app.core.interfaces import (
    IKeywordEngine,
    IBrowserManager,
    IDebugCollector,
    IStepExecutor,
    ITaskOrchestrator
)


# ============================================================================
# Mock 工厂函数
# ============================================================================

def create_mock_keyword_engine() -> IKeywordEngine:
    """创建 Mock 关键字引擎"""
    mock_engine = Mock(spec=IKeywordEngine)
    mock_engine.execute = AsyncMock(return_value={
        "success": True,
        "data": {"result": "ok"}
    })
    return mock_engine


def create_mock_browser_manager() -> IBrowserManager:
    """创建 Mock 浏览器管理器"""
    mock_browser = Mock(spec=IBrowserManager)
    mock_browser.start_browser = AsyncMock()
    mock_browser.close = AsyncMock()
    mock_browser.get_page = AsyncMock(return_value=MagicMock())
    mock_browser.screenshot = AsyncMock()
    return mock_browser


def create_mock_debug_collector() -> IDebugCollector:
    """创建 Mock 调试收集器"""
    mock_collector = Mock(spec=IDebugCollector)
    mock_collector.start_session = Mock()
    mock_collector.setup_page_listeners = AsyncMock()
    mock_collector.collect_failure_info = AsyncMock(return_value={
        "screenshot": "base64...",
        "console_logs": [],
        "network_requests": []
    })
    mock_collector.stop_session = Mock()
    mock_collector.get_session_info = Mock(return_value={})
    return mock_collector


def create_mock_step_executor() -> IStepExecutor:
    """创建 Mock 步骤执行器"""
    mock_executor = Mock(spec=IStepExecutor)
    mock_executor.execute_step = AsyncMock(return_value=MagicMock(
        status="passed",
        result="pass"
    ))
    return mock_executor


def create_mock_task_orchestrator() -> ITaskOrchestrator:
    """创建 Mock 任务编排器"""
    mock_orchestrator = Mock(spec=ITaskOrchestrator)
    mock_orchestrator.orchestrate_task_execution = AsyncMock(
        return_value=MagicMock(
            status="completed",
            result="pass",
            total_steps=10,
            passed_steps=10,
            failed_steps=0
        )
    )
    return mock_orchestrator


# ============================================================================
# 测试示例
# ============================================================================

class TestInterfaceAbstraction:
    """接口抽象测试"""

    @pytest.mark.asyncio
    async def test_keyword_engine_interface(self):
        """测试关键字引擎接口"""
        # 创建 Mock 实现
        mock_engine = create_mock_keyword_engine()

        # 测试调用
        result = await mock_engine.execute(
            keyword_def=MagicMock(name="CLICK"),
            parameters={"selector": "#button"},
            context={"page": MagicMock()}
        )

        # 验证结果
        assert result["success"] is True
        assert result["data"]["result"] == "ok"

        # 验证调用
        mock_engine.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_browser_manager_interface(self):
        """测试浏览器管理接口"""
        # 创建 Mock 实现
        mock_browser = create_mock_browser_manager()

        # 测试启动
        await mock_browser.start_browser()
        mock_browser.start_browser.assert_called_once()

        # 测试获取页面
        page = await mock_browser.get_page()
        mock_browser.get_page.assert_called_once()

        # 测试截图
        await mock_browser.screenshot("/path/to/screenshot.png")
        mock_browser.screenshot.assert_called_once_with("/path/to/screenshot.png")

        # 测试关闭
        await mock_browser.close()
        mock_browser.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_debug_collector_interface(self):
        """测试调试收集接口"""
        # 创建 Mock 实现
        mock_collector = create_mock_debug_collector()

        # 测试启动会话
        mock_collector.start_session("session-123")
        mock_collector.start_session.assert_called_once_with("session-123")

        # 测试设置监听器
        await mock_collector.setup_page_listeners(MagicMock())
        mock_collector.setup_page_listeners.assert_called_once()

        # 测试收集失败信息
        debug_info = await mock_collector.collect_failure_info(
            page=MagicMock(),
            step_execution=MagicMock()
        )
        assert "screenshot" in debug_info
        mock_collector.collect_failure_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_step_executor_interface(self):
        """测试步骤执行器接口"""
        # 创建 Mock 实现
        mock_executor = create_mock_step_executor()

        # 测试执行步骤
        result = await mock_executor.execute_step(
            step=MagicMock(),
            case_execution=MagicMock(),
            scenario_execution=MagicMock(),
            task_execution=MagicMock()
        )

        # 验证结果
        assert result.status == "passed"
        mock_executor.execute_step.assert_called_once()

    @pytest.mark.asyncio
    async def test_task_orchestrator_interface(self):
        """测试任务编排器接口"""
        # 创建 Mock 实现
        mock_orchestrator = create_mock_task_orchestrator()

        # 测试编排任务执行
        result = await mock_orchestrator.orchestrate_task_execution(
            task=MagicMock(),
            execution=MagicMock(),
            browser_config={"headless": True}
        )

        # 验证结果
        assert result.status == "completed"
        assert result.total_steps == 10
        assert result.failed_steps == 0
        mock_orchestrator.orchestrate_task_execution.assert_called_once()


# ============================================================================
# 集成测试示例
# ============================================================================

class TestIntegrationWithMocks:
    """使用 Mock 的集成测试示例"""

    @pytest.mark.asyncio
    async def test_task_execution_with_mocks(self):
        """测试完整的任务执行流程（使用 Mock）"""
        # 创建所有 Mock 组件
        mock_keyword_engine = create_mock_keyword_engine()
        mock_browser = create_mock_browser_manager()
        mock_collector = create_mock_debug_collector()
        mock_step_executor = create_mock_step_executor()
        mock_orchestrator = create_mock_task_orchestrator()

        # 模拟执行流程
        await mock_browser.start_browser()
        mock_collector.start_session("test-session")

        # 执行任务（通过编排器）
        result = await mock_orchestrator.orchestrate_task_execution(
            task=MagicMock(),
            execution=MagicMock(),
            browser_config={"headless": True}
        )

        # 验证结果
        assert result.status == "completed"
        assert result.total_steps == 10
        assert result.failed_steps == 0

        # 清理
        await mock_browser.close()
        mock_collector.stop_session()

        # 验证所有调用
        mock_browser.start_browser.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_collector.start_session.assert_called_once()
        mock_collector.stop_session.assert_called_once()


# ============================================================================
# 实际使用示例
# ============================================================================

class TestRealImplementation:
    """使用真实实现的测试示例"""

    @pytest.mark.asyncio
    async def test_step_executor_with_real_components(self):
        """测试 StepExecutor 可以使用接口调用"""
        from app.services.execution.step_executor import StepExecutor

        # 创建 Mock 依赖（可以轻松替换任何组件）
        mock_db = MagicMock()
        mock_keyword_engine = create_mock_keyword_engine()
        mock_browser = create_mock_browser_manager()
        mock_collector = create_mock_debug_collector()

        # 创建 StepExecutor（使用接口）
        executor = TaskExecutor(
            db=mock_db,
            keyword_engine=mock_keyword_engine,  # IKeywordEngine 接口
            browser_manager=mock_browser,          # IBrowserManager 接口
            debug_collector=mock_collector         # IDebugCollector 接口
        )

        # 验证可以正常工作
        assert executor.keyword_engine is not None
        assert executor.browser_manager is not None
        assert executor.debug_collector is not None


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])


# ============================================================================
# 使用示例（独立脚本）
# ============================================================================

async def demonstrate_interface_usage():
    """演示接口使用方式"""

    print("=" * 60)
    print("接口抽象演示")
    print("=" * 60)

    # 1. 创建 Mock 实现
    print("\n1. 创建 Mock 实现...")
    mock_keyword_engine = create_mock_keyword_engine()
    mock_browser = create_mock_browser_manager()
    mock_collector = create_mock_debug_collector()

    # 2. 使用接口（不依赖具体实现）
    print("\n2. 使用接口调用...")
    await mock_browser.start_browser()
    print("   ✓ 浏览器已启动")

    result = await mock_keyword_engine.execute(
        keyword_def=MagicMock(name="CLICK"),
        parameters={"selector": "#button"},
        context={"page": MagicMock()}
    )
    print(f"   ✓ 关键字执行结果: {result}")

    mock_collector.start_session("demo-session")
    print("   ✓ 调试会话已启动")

    # 3. 清理
    await mock_browser.close()
    mock_collector.stop_session()
    print("   ✓ 资源已清理")

    print("\n" + "=" * 60)
    print("接口抽象优势：")
    print("  ✓ 解耦：模块间依赖抽象，而非具体实现")
    print("  ✓ 可测试：轻松 Mock 任何依赖")
    print("  ✓ 可扩展：轻松替换不同实现")
    print("  ✓ 灵活：运行时选择具体实现")
    print("=" * 60)


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demonstrate_interface_usage())
