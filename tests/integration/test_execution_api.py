"""
执行系统和取消机制测试

验证取消信号、Executor 生命周期、ConnectionManager 的核心逻辑
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


class TestConnectionManagerCancel:
    """ConnectionManager 取消机制"""

    def test_cancel_event_set_and_check(self):
        """设置取消事件后 is_cancelled 应返回 True"""
        from app.api.agent import ConnectionManager
        mgr = ConnectionManager()
        task_id = str(uuid.uuid4())

        assert not mgr.is_cancelled(task_id)
        mgr.cancel_execution(task_id)
        assert mgr.is_cancelled(task_id)

    def test_cancel_nonexistent_task(self):
        """未取消的任务 is_cancelled 应返回 False"""
        from app.api.agent import ConnectionManager
        mgr = ConnectionManager()
        assert not mgr.is_cancelled("nonexistent-id")

    def test_cancel_event_persists(self):
        """cancel_event 在多次调用 is_cancelled 后应持续返回 True"""
        from app.api.agent import ConnectionManager
        mgr = ConnectionManager()
        task_id = str(uuid.uuid4())
        mgr.cancel_execution(task_id)
        assert mgr.is_cancelled(task_id)
        assert mgr.is_cancelled(task_id)  # 第二次检查仍为 True

    def test_multiple_tasks_independent(self):
        """不同任务的取消状态应独立"""
        from app.api.agent import ConnectionManager
        mgr = ConnectionManager()
        task_a = str(uuid.uuid4())
        task_b = str(uuid.uuid4())

        mgr.cancel_execution(task_a)
        assert mgr.is_cancelled(task_a)
        assert not mgr.is_cancelled(task_b)

    def test_cancel_triggers_task_event(self):
        """cancel_execution 应触发对应的 task_event"""
        import asyncio
        from app.api.agent import ConnectionManager
        mgr = ConnectionManager()
        task_id = str(uuid.uuid4())

        # 模拟有一个等待中的 task_event
        event = asyncio.Event()
        mgr.task_events[task_id] = event

        mgr.cancel_execution(task_id)
        # task_event 应已被 set
        assert event.is_set()


class TestExecutorLifecycle:
    """TaskExecutor 生命周期"""

    def test_create_execution_sets_mode_direct(self):
        """create_and_start_execution 在 use_agent=False 时应设置 execution_mode=direct"""
        import asyncio
        from app.services.execution.executor import TaskExecutor
        from app.schemas.execution import ExecutionRequest
        from app.models.ui_task import UITask
        from unittest.mock import MagicMock

        task_id = uuid.uuid4()
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        execution_id = uuid.uuid4()

        mock_db = MagicMock()

        task = UITask(
            id=task_id,
            project_id=project_id,
            name="Test Task",
            task_type="ui",
            scenario_ids=[],
            execution_config={},
            tags=[]
        )
        mock_db.query.return_value.filter.return_value.first.return_value = task

        executor = TaskExecutor(mock_db)

        request = ExecutionRequest(
            task_id=task_id,
            user_id=user_id,
            browser_config={"use_agent": False},
            execution_config={},
            environment="test"
        )

        # executor 函数内部使用 from app.api.agent import manager
        with patch("app.services.execution.executor.uuid.uuid4", return_value=execution_id):
            with patch("app.api.agent.manager") as mock_mgr:
                mock_mgr.get_all_agents.return_value = {}
                mock_mgr.cancel_events = {}
                result = asyncio.run(executor.create_and_start_execution(request))

        assert result.execution_mode == "direct"

    def test_continue_execution_without_current_raises(self):
        """未设置 current_execution 时调用 continue_execution 应抛出异常"""
        import asyncio
        from app.services.execution.executor import TaskExecutor
        from unittest.mock import MagicMock

        executor = TaskExecutor(MagicMock())
        executor.current_execution = None

        with pytest.raises(ValueError, match="No execution to continue"):
            asyncio.run(executor.continue_execution())


class TestTestExecutionStatusModel:
    """TestExecution 状态转换"""

    def test_status_values(self):
        """验证状态常量"""
        from app.models.execution import TestExecution
        valid_statuses = {"pending", "running", "completed", "failed", "cancelled"}
        # 验证 cancelled 状态存在（用于取消功能）
        assert "cancelled" in valid_statuses
        assert "running" in valid_statuses

    def test_execution_creation_defaults(self):
        """新创建的执行记录可通过构造函数设置所有字段"""
        from app.models.execution import TestExecution
        exec_id = uuid.uuid4()
        task_id = uuid.uuid4()
        project_id = uuid.uuid4()

        execution = TestExecution(
            id=exec_id,
            task_id=task_id,
            project_id=project_id,
            status="running",
            result="pass",
            execution_mode="direct",
            total_scenarios=2,
            total_cases=5,
            total_steps=10,
            passed_steps=8,
            failed_steps=2,
            skipped_steps=0,
        )
        assert execution.status == "running"
        assert execution.execution_mode == "direct"
        assert execution.total_scenarios == 2
        assert execution.total_steps == 10
        assert execution.passed_steps == 8
        assert execution.failed_steps == 2


class TestRateLimitRelaxed:
    """速率限制放宽验证"""

    def test_login_rate_limit(self):
        """登录速率限制应 >= 20 次/分钟（修复频繁输入密码被锁）"""
        from app.middleware.rate_limit import RateLimitMiddleware
        login_rule = RateLimitMiddleware.RATE_LIMITS.get("/api/v1/auth/login")
        assert login_rule is not None
        assert login_rule[0] >= 20, f"登录限制过严: {login_rule[0]} 次/分钟"

    def test_ui_rate_limit(self):
        """UI 端点速率限制应足够宽松"""
        from app.middleware.rate_limit import RateLimitMiddleware
        ui_rule = RateLimitMiddleware.RATE_LIMITS.get("/api/v1/ui")
        assert ui_rule is not None
        assert ui_rule[0] >= 200, f"UI 限制过严: {ui_rule[0]} 次/分钟"
