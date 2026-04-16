"""
执行器协议

定义任务执行器的接口
"""
from typing import Protocol, Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExecutionResult:
    """
    执行结果

    Attributes:
        success: 是否成功
        status: 执行状态 (running, completed, failed, cancelled)
        message: 结果消息
        statistics: 统计信息
        error: 错误信息（失败时）
        started_at: 开始时间
        completed_at: 完成时间
        duration: 执行时长（毫秒）
    """
    success: bool
    status: str
    message: str
    statistics: Dict[str, Any]
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "status": self.status,
            "message": self.message,
            "statistics": self.statistics,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration
        }


class TaskExecutorProtocol(Protocol):
    """
    任务执行器协议

    定义任务执行的标准接口
    """

    async def prepare_task(self, task_id: str) -> Dict[str, Any]:
        """
        准备任务执行

        Args:
            task_id: 任务 ID

        Returns:
            任务数据字典（包含场景、用例、步骤）
        """
        ...

    async def validate_task(self, task_data: Dict[str, Any]) -> None:
        """
        验证任务数据

        Args:
            task_data: 任务数据

        Raises:
            ValueError: 验证失败
        """
        ...

    async def execute_task(
        self,
        task_id: str,
        execution_config: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        执行任务

        Args:
            task_id: 任务 ID
            execution_config: 执行配置

        Returns:
            ExecutionResult: 执行结果
        """
        ...

    async def cancel_execution(self, execution_id: str) -> bool:
        """
        取消执行

        Args:
            execution_id: 执行 ID

        Returns:
            是否成功取消
        """
        ...

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        获取执行状态

        Args:
            execution_id: 执行 ID

        Returns:
            执行状态信息
        """
        ...


class ScenarioExecutor(Protocol):
    """
    场景执行器协议
    """

    async def execute_scenario(
        self,
        scenario_data: Dict[str, Any],
        context: 'ExecutionContext'  # noqa: F821
    ) -> Dict[str, Any]:
        """
        执行场景

        Args:
            scenario_data: 场景数据
            context: 执行上下文

        Returns:
            场景执行结果
        """
        ...


class CaseExecutor(Protocol):
    """
    用例执行器协议
    """

    async def execute_case(
        self,
        case_data: Dict[str, Any],
        context: 'ExecutionContext'  # noqa: F821
    ) -> Dict[str, Any]:
        """
        执行用例

        Args:
            case_data: 用例数据
            context: 执行上下文

        Returns:
            用例执行结果
        """
        ...


class StepExecutor(Protocol):
    """
    步骤执行器协议
    """

    async def execute_step(
        self,
        step_data: Dict[str, Any],
        context: 'ExecutionContext'  # noqa: F821
    ) -> Dict[str, Any]:
        """
        执行步骤

        Args:
            step_data: 步骤数据
            context: 执行上下文

        Returns:
            步骤执行结果
        """
        ...
