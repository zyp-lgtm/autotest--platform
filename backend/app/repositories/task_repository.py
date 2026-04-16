"""
任务仓储

处理 UI 任务、场景、用例、步骤的数据访问
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid
import logging

from app.repositories.base import BaseRepository
from app.models.ui_task import UITask, UIScenario, UICase, UIStep

logger = logging.getLogger(__name__)


class TaskRepository(BaseRepository):
    """UI 任务仓储"""

    def __init__(self, session: Session):
        super().__init__(session, UITask)

    def get_by_project(
        self,
        project_id: str,
        limit: Optional[int] = None,
        order_by_desc: bool = True
    ) -> List[UITask]:
        """
        获取项目的所有任务

        Args:
            project_id: 项目 ID
            limit: 限制返回数量
            order_by_desc: 是否按创建时间倒序排列

        Returns:
            任务列表
        """
        try:
            project_uuid = uuid.UUID(project_id)
        except ValueError:
            logger.warning(f"无效的项目ID格式: {project_id}")
            return []

        query = self.session.query(UITask).filter(UITask.project_id == project_uuid)

        if order_by_desc:
            query = query.order_by(desc(UITask.created_at))

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_with_scenarios(self, task_id: str) -> Optional[UITask]:
        """
        获取任务及其场景（预加载，避免 N+1 查询）

        Args:
            task_id: 任务 ID

        Returns:
            任务对象，包含预加载的场景
        """
        try:
            task_uuid = uuid.UUID(task_id)
        except ValueError:
            logger.warning(f"无效的任务ID格式: {task_id}")
            return None

        return self.session.query(UITask).filter(
            UITask.id == task_uuid
        ).first()

    def add_scenario(self, task_id: str, scenario_id: str) -> bool:
        """
        向任务添加场景

        Args:
            task_id: 任务 ID
            scenario_id: 场景 ID

        Returns:
            是否添加成功
        """
        task = self.get_by_id(task_id)
        if not task:
            return False

        if not task.scenario_ids:
            task.scenario_ids = []

        scenario_str = str(scenario_id).replace('-', '')
        if scenario_str not in task.scenario_ids:
            task.scenario_ids.append(scenario_str)
            self.session.commit()

        return True

    def remove_scenario(self, task_id: str, scenario_id: str) -> bool:
        """
        从任务移除场景

        Args:
            task_id: 任务 ID
            scenario_id: 场景 ID

        Returns:
            是否移除成功
        """
        task = self.get_by_id(task_id)
        if not task or not task.scenario_ids:
            return False

        scenario_str = str(scenario_id).replace('-', '')
        if scenario_str in task.scenario_ids:
            task.scenario_ids.remove(scenario_str)
            self.session.commit()

        return True


class ScenarioRepository(BaseRepository):
    """场景仓储"""

    def __init__(self, session: Session):
        super().__init__(session, UIScenario)

    def get_by_task(self, task_id: str) -> List[UIScenario]:
        """
        获取任务的所有场景

        Args:
            task_id: 任务 ID

        Returns:
            场景列表（按执行顺序排序）
        """
        try:
            task_uuid = uuid.UUID(task_id)
        except ValueError:
            logger.warning(f"无效的任务ID格式: {task_id}")
            return []

        return self.session.query(UIScenario).filter(
            UIScenario.task_id == task_uuid
        ).order_by(UIScenario.execution_order).all()

    def get_with_cases(self, scenario_id: str) -> Optional[UIScenario]:
        """
        获取场景及其用例

        Args:
            scenario_id: 场景 ID

        Returns:
            场景对象
        """
        return self.get_by_id(scenario_id)

    def add_case(self, scenario_id: str, case_id: str) -> bool:
        """
        向场景添加用例

        Args:
            scenario_id: 场景 ID
            case_id: 用例 ID

        Returns:
            是否添加成功
        """
        scenario = self.get_by_id(scenario_id)
        if not scenario:
            return False

        if not scenario.case_ids:
            scenario.case_ids = []

        case_str = str(case_id).replace('-', '')
        if case_str not in scenario.case_ids:
            scenario.case_ids.append(case_str)
            self.session.commit()

        return True

    def remove_case(self, scenario_id: str, case_id: str) -> bool:
        """
        从场景移除用例

        Args:
            scenario_id: 场景 ID
            case_id: 用例 ID

        Returns:
            是否移除成功
        """
        scenario = self.get_by_id(scenario_id)
        if not scenario or not scenario.case_ids:
            return False

        case_str = str(case_id).replace('-', '')
        if case_str in scenario.case_ids:
            scenario.case_ids.remove(case_str)
            self.session.commit()

        return True

    def get_next_execution_order(self, task_id: str) -> int:
        """
        获取下一个执行顺序号

        Args:
            task_id: 任务 ID

        Returns:
            下一个顺序号
        """
        try:
            task_uuid = uuid.UUID(task_id)
        except ValueError:
            return 0

        count = self.session.query(UIScenario).filter(
            UIScenario.task_id == task_uuid
        ).count()

        return count


class CaseRepository(BaseRepository):
    """用例仓储"""

    def __init__(self, session: Session):
        super().__init__(session, UICase)

    def get_by_scenario(self, scenario_id: str) -> List[UICase]:
        """
        获取场景的所有用例

        Args:
            scenario_id: 场景 ID

        Returns:
            用例列表
        """
        try:
            scenario_uuid = uuid.UUID(scenario_id)
        except ValueError:
            logger.warning(f"无效的场景ID格式: {scenario_id}")
            return []

        return self.session.query(UICase).filter(
            UICase.scenario_id == scenario_uuid
        ).all()

    def get_with_steps(self, case_id: str) -> Optional[UICase]:
        """
        获取用例及其步骤

        Args:
            case_id: 用例 ID

        Returns:
            用例对象
        """
        return self.get_by_id(case_id)

    def add_step(self, case_id: str, step_id: str) -> bool:
        """
        向用例添加步骤

        Args:
            case_id: 用例 ID
            step_id: 步骤 ID

        Returns:
            是否添加成功
        """
        case_item = self.get_by_id(case_id)
        if not case_item:
            return False

        if not case_item.step_ids:
            case_item.step_ids = []

        step_str = str(step_id).replace('-', '')
        if step_str not in case_item.step_ids:
            case_item.step_ids.append(step_str)
            self.session.commit()

        return True

    def remove_step(self, case_id: str, step_id: str) -> bool:
        """
        从用例移除步骤

        Args:
            case_id: 用例 ID
            step_id: 步骤 ID

        Returns:
            是否移除成功
        """
        case_item = self.get_by_id(case_id)
        if not case_item or not case_item.step_ids:
            return False

        step_str = str(step_id).replace('-', '')
        if step_str in case_item.step_ids:
            case_item.step_ids.remove(step_str)
            self.session.commit()

        return True


class StepRepository(BaseRepository):
    """步骤仓储"""

    def __init__(self, session: Session):
        super().__init__(session, UIStep)

    def get_by_case(self, case_id: str) -> List[UIStep]:
        """
        获取用例的所有步骤

        Args:
            case_id: 用例 ID

        Returns:
            步骤列表（按步骤顺序排序）
        """
        try:
            case_uuid = uuid.UUID(case_id)
        except ValueError:
            logger.warning(f"无效的用例ID格式: {case_id}")
            return []

        return self.session.query(UIStep).filter(
            UIStep.case_id == case_uuid
        ).order_by(UIStep.step_order).all()

    def get_by_scenario(self, scenario_id: str) -> List[UIStep]:
        """
        获取场景的所有步骤

        Args:
            scenario_id: 场景 ID

        Returns:
            步骤列表
        """
        try:
            scenario_uuid = uuid.UUID(scenario_id)
        except ValueError:
            logger.warning(f"无效的场景ID格式: {scenario_id}")
            return []

        return self.session.query(UIStep).filter(
            UIStep.scenario_id == scenario_uuid
        ).order_by(UIStep.step_order).all()

    def get_by_task(self, task_id: str) -> List[UIStep]:
        """
        获取任务的所有步骤

        Args:
            task_id: 任务 ID

        Returns:
            步骤列表
        """
        try:
            task_uuid = uuid.UUID(task_id)
        except ValueError:
            logger.warning(f"无效的任务ID格式: {task_id}")
            return []

        return self.session.query(UIStep).filter(
            UIStep.task_id == task_uuid
        ).order_by(UIStep.step_order).all()

    def get_next_step_order(self, case_id: str) -> int:
        """
        获取下一个步骤顺序号

        Args:
            case_id: 用例 ID

        Returns:
            下一个顺序号
        """
        try:
            case_uuid = uuid.UUID(case_id)
        except ValueError:
            return 0

        count = self.session.query(UIStep).filter(
            UIStep.case_id == case_uuid
        ).count()

        return count
