"""
执行仓储

处理测试执行记录的数据访问
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc
import uuid
import logging

from app.repositories.base import BaseRepository
from app.models.execution import TestExecution, ScenarioExecution, CaseExecution, StepExecution

logger = logging.getLogger(__name__)


class ExecutionRepository(BaseRepository):
    """测试执行仓储"""

    def __init__(self, session: Session):
        super().__init__(session, TestExecution)

    def get_by_task(
        self,
        task_id: str,
        limit: int = 10
    ) -> List[TestExecution]:
        """
        获取任务的执行记录

        Args:
            task_id: 任务 ID
            limit: 限制返回数量

        Returns:
            执行记录列表（按创建时间倒序）
        """
        try:
            task_uuid = uuid.UUID(task_id)
        except ValueError:
            logger.warning(f"无效的任务ID格式: {task_id}")
            return []

        return self.session.query(TestExecution).filter(
            TestExecution.task_id == task_uuid
        ).order_by(desc(TestExecution.created_at)).limit(limit).all()

    def get_with_details(self, execution_id: str) -> Optional[TestExecution]:
        """
        获取执行记录及其详细信息（预加载所有关联数据）

        Args:
            execution_id: 执行记录 ID

        Returns:
            执行记录对象（包含预加载的场景、用例、步骤执行记录）
        """
        try:
            exec_uuid = uuid.UUID(execution_id)
        except ValueError:
            logger.warning(f"无效的执行ID格式: {execution_id}")
            return None

        # 使用 selectinload 预加载所有关联数据，避免 N+1 查询
        return self.session.query(TestExecution).options(
            selectinload(TestExecution.scenario_executions)
            .selectinload(ScenarioExecution.case_executions)
            .selectinload(CaseExecution.step_executions)
        ).filter(TestExecution.id == exec_uuid).first()

    def get_recent_by_project(
        self,
        project_id: str,
        limit: int = 20
    ) -> List[TestExecution]:
        """
        获取项目的最近执行记录

        Args:
            project_id: 项目 ID
            limit: 限制返回数量

        Returns:
            执行记录列表
        """
        try:
            project_uuid = uuid.UUID(project_id)
        except ValueError:
            logger.warning(f"无效的项目ID格式: {project_id}")
            return []

        return self.session.query(TestExecution).filter(
            TestExecution.project_id == project_uuid
        ).order_by(desc(TestExecution.created_at)).limit(limit).all()

    def get_statistics_by_task(self, task_id: str) -> dict:
        """
        获取任务的执行统计信息

        Args:
            task_id: 任务 ID

        Returns:
            统计信息字典
        """
        executions = self.get_by_task(task_id, limit=1000)

        total = len(executions)
        passed = sum(1 for e in executions if e.result == "passed")
        failed = sum(1 for e in executions if e.result == "failed")
        running = sum(1 for e in executions if e.status == "running")

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "running": running,
            "pass_rate": passed / total if total > 0 else 0
        }


class ScenarioExecutionRepository(BaseRepository):
    """场景执行仓储"""

    def __init__(self, session: Session):
        super().__init__(session, ScenarioExecution)

    def get_by_test_execution(self, test_execution_id: str) -> List[ScenarioExecution]:
        """
        获取测试执行的场景执行记录

        Args:
            test_execution_id: 测试执行 ID

        Returns:
            场景执行记录列表（按执行顺序排序）
        """
        try:
            exec_uuid = uuid.UUID(test_execution_id)
        except ValueError:
            logger.warning(f"无效的执行ID格式: {test_execution_id}")
            return []

        return self.session.query(ScenarioExecution).filter(
            ScenarioExecution.test_execution_id == exec_uuid
        ).order_by(ScenarioExecution.execution_order).all()

    def get_with_cases(self, scenario_exec_id: str) -> Optional[ScenarioExecution]:
        """
        获取场景执行及其用例执行

        Args:
            scenario_exec_id: 场景执行 ID

        Returns:
            场景执行对象
        """
        try:
            exec_uuid = uuid.UUID(scenario_exec_id)
        except ValueError:
            logger.warning(f"无效的场景执行ID格式: {scenario_exec_id}")
            return None

        return self.session.query(ScenarioExecution).options(
            selectinload(ScenarioExecution.case_executions)
            .selectinload(CaseExecution.step_executions)
        ).filter(ScenarioExecution.id == exec_uuid).first()


class CaseExecutionRepository(BaseRepository):
    """用例执行仓储"""

    def __init__(self, session: Session):
        super().__init__(session, CaseExecution)

    def get_by_scenario_execution(self, scenario_exec_id: str) -> List[CaseExecution]:
        """
        获取场景执行的用例执行记录

        Args:
            scenario_exec_id: 场景执行 ID

        Returns:
            用例执行记录列表
        """
        try:
            exec_uuid = uuid.UUID(scenario_exec_id)
        except ValueError:
            logger.warning(f"无效的场景执行ID格式: {scenario_exec_id}")
            return []

        return self.session.query(CaseExecution).filter(
            CaseExecution.scenario_execution_id == exec_uuid
        ).all()

    def get_with_steps(self, case_exec_id: str) -> Optional[CaseExecution]:
        """
        获取用例执行及其步骤执行

        Args:
            case_exec_id: 用例执行 ID

        Returns:
            用例执行对象
        """
        try:
            exec_uuid = uuid.UUID(case_exec_id)
        except ValueError:
            logger.warning(f"无效的用例执行ID格式: {case_exec_id}")
            return None

        return self.session.query(CaseExecution).options(
            selectinload(CaseExecution.step_executions)
        ).filter(CaseExecution.id == exec_uuid).first()


class StepExecutionRepository(BaseRepository):
    """步骤执行仓储"""

    def __init__(self, session: Session):
        super().__init__(session, StepExecution)

    def get_by_case_execution(self, case_exec_id: str) -> List[StepExecution]:
        """
        获取用例执行的步骤执行记录

        Args:
            case_exec_id: 用例执行 ID

        Returns:
            步骤执行记录列表（按步骤顺序排序）
        """
        try:
            exec_uuid = uuid.UUID(case_exec_id)
        except ValueError:
            logger.warning(f"无效的用例执行ID格式: {case_exec_id}")
            return []

        return self.session.query(StepExecution).filter(
            StepExecution.case_execution_id == exec_uuid
        ).order_by(StepExecution.step_order).all()

    def get_failed_steps(self, test_execution_id: str) -> List[StepExecution]:
        """
        获取执行记录中的所有失败步骤

        Args:
            test_execution_id: 测试执行 ID

        Returns:
            失败步骤列表
        """
        try:
            exec_uuid = uuid.UUID(test_execution_id)
        except ValueError:
            logger.warning(f"无效的执行ID格式: {test_execution_id}")
            return []

        return self.session.query(StepExecution).join(
            CaseExecution
        ).join(
            ScenarioExecution
        ).filter(
            ScenarioExecution.test_execution_id == exec_uuid,
            StepExecution.result == "failed"
        ).all()

    def get_screenshots(self, test_execution_id: str) -> List[str]:
        """
        获取执行记录的所有截图路径

        Args:
            test_execution_id: 测试执行 ID

        Returns:
            截图路径列表
        """
        try:
            exec_uuid = uuid.UUID(test_execution_id)
        except ValueError:
            return []

        steps = self.session.query(StepExecution.screenshot_path).join(
            CaseExecution
        ).join(
            ScenarioExecution
        ).filter(
            ScenarioExecution.test_execution_id == exec_uuid,
            StepExecution.screenshot_path.isnot(None)
        ).all()

        return [step[0] for step in steps if step[0]]
