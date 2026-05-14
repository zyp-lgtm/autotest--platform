"""
接口抽象层

使用 Protocol（结构化子类型）定义核心接口，解耦模块依赖。
这遵循依赖倒置原则（DIP）：高层模块不应依赖低层模块，都应依赖抽象。

## 设计原则

1. **依赖倒置原则 (DIP)**: 依赖抽象而非具体实现
2. **接口隔离原则 (ISP)**: 接口小而专注
3. **开闭原则 (OCP)**: 对扩展开放，对修改关闭

## 使用方式

```python
from app.core.interfaces import IKeywordEngine, IBrowserManager

# 使用接口类型提示
class TaskExecutor:
    def __init__(
        self,
        keyword_engine: IKeywordEngine,  # 依赖抽象
        browser_manager: IBrowserManager  # 依赖抽象
    ):
        self.keyword_engine = keyword_engine
        self.browser_manager = browser_manager
```
"""

from typing import Protocol, Dict, Any, Optional, List
from playwright.async_api import Page
from sqlalchemy.orm import Session


# ============================================================================
# 关键字引擎接口
# ============================================================================

class IKeywordEngine(Protocol):
    """
    关键字引擎接口

    定义关键字执行的抽象接口，解耦具体实现。
    任何实现此接口的类都可以作为关键字引擎使用。
    """

    async def execute(
        self,
        keyword_def: Any,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行关键字

        Args:
            keyword_def: 关键字定义
            parameters: 参数字典
            context: 执行上下文（page, browser_manager 等）

        Returns:
            执行结果，包含 success 和 data/error 字段
        """
        ...


# ============================================================================
# 浏览器管理接口
# ============================================================================

class IBrowserManager(Protocol):
    """
    浏览器管理接口

    定义浏览器生命周期管理的抽象接口。
    支持多种浏览器实现（Playwright, Selenium 等）。
    """

    async def start_browser(self) -> None:
        """启动浏览器"""
        ...

    async def close(self) -> None:
        """关闭浏览器和所有资源"""
        ...

    async def get_page(self) -> Page:
        """
        获取当前活动页面

        Returns:
            Playwright Page 对象
        """
        ...

    async def screenshot(self, path: str, full_page: bool = False) -> None:
        """
        截图

        Args:
            path: 截图保存路径
            full_page: 是否截取完整页面
        """
        ...


# ============================================================================
# 调试信息收集接口
# ============================================================================

class IDebugCollector(Protocol):
    """
    调试信息收集接口

    定义调试信息收集的抽象接口。
    可以有多种实现（本地收集、远程收集、无操作等）。
    """

    def start_session(self, session_id: str) -> None:
        """启动调试会话"""
        ...

    async def setup_page_listeners(self, page: Page) -> None:
        """设置页面监听器（控制台、网络等）"""
        ...

    async def collect_failure_info(
        self,
        page: Page,
        step_execution: Any
    ) -> Dict[str, Any]:
        """
        收集失败时的调试信息

        Args:
            page: Playwright Page 对象
            step_execution: 步骤执行记录

        Returns:
            调试信息字典（截图、日志、网络请求等）
        """
        ...

    def stop_session(self) -> None:
        """停止调试会话"""
        ...

    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        ...


# ============================================================================
# 步骤执行器接口
# ============================================================================

class IStepExecutor(Protocol):
    """
    步骤执行器接口

    定义单个步骤执行的抽象接口。
    """

    async def execute_step(
        self,
        step: Any,
        case_execution: Any,
        scenario_execution: Any,
        task_execution: Any,
        case: Any = None,
        data_row_index: int = 0
    ) -> Any:
        """
        执行单个步骤

        Args:
            step: 步骤定义
            case_execution: 用例执行记录
            scenario_execution: 场景执行记录
            task_execution: 任务执行记录
            case: 用例定义（可选）
            data_row_index: 数据行索引（默认 0）

        Returns:
            步骤执行记录
        """
        ...


# ============================================================================
# 任务编排器接口
# ============================================================================

class ITaskOrchestrator(Protocol):
    """
    任务编排器接口

    定义任务执行流程编排的抽象接口。
    """

    async def orchestrate_task_execution(
        self,
        task: Any,
        execution: Any,
        browser_config: Dict[str, Any]
    ) -> Any:
        """
        编排并执行任务

        Args:
            task: 任务定义
            execution: 执行记录
            browser_config: 浏览器配置

        Returns:
            更新后的执行记录
        """
        ...


# ============================================================================
# 数据仓库接口（未来扩展）
# ============================================================================

class ITaskRepository(Protocol):
    """
    任务数据仓库接口

    定义任务数据访问的抽象接口。
    解耦业务逻辑和数据访问层。
    """

    def get_by_id(self, task_id: str, db: Session) -> Optional[Any]:
        """根据 ID 获取任务"""
        ...

    def get_scenarios(self, task_id: str, db: Session) -> List[Any]:
        """获取任务的所有场景"""
        ...

    def create_execution(
        self,
        task_id: str,
        project_id: str,
        user_id: Optional[str],
        db: Session
    ) -> Any:
        """创建执行记录"""
        ...


# ============================================================================
# 代理管理接口（未来扩展）
# ============================================================================

class IAgentManager(Protocol):
    """
    代理管理接口

    定义 Agent 管理的抽象接口。
    支持多种 Agent 实现。
    """

    async def send_task_to_agent(
        self,
        agent_id: str,
        task_data: Dict[str, Any],
        browser_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """发送任务给 Agent"""
        ...

    def get_all_agents(self) -> Dict[str, Any]:
        """获取所有可用 Agent"""
        ...


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 示例：使用接口编写可测试的代码

    from unittest.mock import Mock

    # 创建 Mock 实现
    mock_keyword_engine = Mock(spec=IKeywordEngine)
    mock_browser_manager = Mock(spec=IBrowserManager)
    mock_debug_collector = Mock(spec=IDebugCollector)

    # 配置 Mock 行为
    mock_keyword_engine.execute.return_value = {
        "success": True,
        "data": {"result": "ok"}
    }

    # 使用接口（不依赖具体实现）
    async def execute_with_interfaces(
        keyword_engine: IKeywordEngine,
        browser_manager: IBrowserManager
    ):
        """使用接口的函数，可以接受任何实现"""
        result = await keyword_engine.execute(
            keyword_def=None,
            parameters={},
            context={"page": await browser_manager.get_page()}
        )
        return result

    # 测试
    import asyncio
    result = asyncio.run(execute_with_interfaces(
        mock_keyword_engine,
        mock_browser_manager
    ))
    print(f"Result: {result}")
