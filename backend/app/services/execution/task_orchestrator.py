"""
任务编排器

负责任务的编排：协调场景、用例、步骤的执行顺序
"""
import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ...models.ui_task import UITask, UIScenario, UICase, UIStep
from ...models.execution import TestExecution, ScenarioExecution, CaseExecution
from .step_executor import StepExecutor
from ...core.interfaces import IStepExecutor

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """任务编排器"""

    def __init__(
        self,
        db: Session,
        step_executor: IStepExecutor  # 使用接口而非具体实现
    ):
        """
        初始化任务编排器

        Args:
            db: 数据库会话
            step_executor: 步骤执行器（接口）
        """
        self.db = db
        self.step_executor = step_executor

    async def orchestrate_task_execution(
        self,
        task: UITask,
        execution: TestExecution,
        browser_config: Dict[str, Any]
    ) -> TestExecution:
        """
        编排并执行任务

        Args:
            task: 任务定义
            execution: 执行记录
            browser_config: 浏览器配置

        Returns:
            TestExecution: 更新后的执行记录
        """
        try:
            # 1. 加载场景
            scenarios = self._load_scenarios(task)

            # 2. 按顺序执行场景
            for scenario_order, scenario in enumerate(scenarios, start=1):
                scenario_execution = await self._orchestrate_scenario_execution(
                    scenario, execution, scenario_order
                )

                # 更新统计
                self._update_execution_stats(execution)

            # 3. 执行完成，更新状态
            execution.status = "completed"
            execution.completed_at = datetime.now(timezone.utc)
            execution.result = "pass" if execution.failed_steps == 0 else "fail"

            # 计算总时长
            started_at = execution.started_at.replace(tzinfo=timezone.utc)
            execution.duration = (
                execution.completed_at - started_at
            ).total_seconds()

            self.db.commit()
            self.db.refresh(execution)

            logger.info(f"任务执行完成: {execution.result} ({execution.passed_steps}/{execution.total_steps} 通过)")

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            execution.status = "failed"
            execution.completed_at = datetime.now(timezone.utc)
            execution.error_message = str(e)
            execution.result = "error"

            # 计算时长
            if execution.started_at:
                started_at = execution.started_at.replace(tzinfo=timezone.utc)
                execution.duration = (
                    execution.completed_at - started_at
                ).total_seconds()

            self.db.commit()
            self.db.refresh(execution)

        return execution

    async def _orchestrate_scenario_execution(
        self,
        scenario: UIScenario,
        task_execution: TestExecution,
        execution_order: int
    ) -> ScenarioExecution:
        """
        编排并执行场景

        Args:
            scenario: 场景定义
            task_execution: 任务执行记录
            execution_order: 执行顺序

        Returns:
            ScenarioExecution: 场景执行记录
        """
        import uuid

        # 创建场景执行记录
        scenario_execution = ScenarioExecution(
            id=uuid.uuid4(),
            test_execution_id=task_execution.id,
            scenario_id=scenario.id,
            status="pending",
            execution_order=execution_order,
            total_cases=0,
            total_steps=0,
            passed_steps=0,
            failed_steps=0
        )
        self.db.add(scenario_execution)
        self.db.commit()

        try:
            # 1. 加载用例
            cases = self._load_cases(scenario)

            # 2. 按顺序执行用例
            for case in cases:
                case_execution = await self._orchestrate_case_execution(
                    case, scenario_execution, task_execution
                )

                # 更新统计
                self._update_scenario_stats(scenario_execution)

            # 更新状态
            scenario_execution.status = "completed"
            scenario_execution.result = "pass" if scenario_execution.failed_steps == 0 else "fail"

            self.db.commit()
            self.db.refresh(scenario_execution)

        except Exception as e:
            logger.error(f"场景执行失败: {e}")
            scenario_execution.status = "failed"
            scenario_execution.result = "fail"
            scenario_execution.error_message = str(e)

            self.db.commit()
            self.db.refresh(scenario_execution)

        return scenario_execution

    async def _orchestrate_case_execution(
        self,
        case: UICase,
        scenario_execution: ScenarioExecution,
        task_execution: TestExecution
    ) -> CaseExecution:
        """
        编排并执行用例

        Args:
            case: 用例定义
            scenario_execution: 场景执行记录
            task_execution: 任务执行记录

        Returns:
            CaseExecution: 用例执行记录
        """
        import uuid

        # 创建用例执行记录
        case_execution = CaseExecution(
            id=uuid.uuid4(),
            scenario_execution_id=scenario_execution.id,
            case_id=case.id,
            status="pending",
            total_steps=0,
            passed_steps=0,
            failed_steps=0
        )
        self.db.add(case_execution)
        self.db.commit()

        try:
            # 1. 加载步骤
            steps = self._load_steps(case)

            case_execution.total_steps = len(steps)
            self.db.flush()

            # 2. 按顺序执行步骤
            for step in steps:
                step_execution = await self.step_executor.execute_step(
                    step, case_execution, scenario_execution, task_execution, case
                )

                # 更新统计
                if step_execution.status == "passed":
                    case_execution.passed_steps += 1
                elif step_execution.status == "failed":
                    case_execution.failed_steps += 1

                    # 检查是否应该停止
                    if not step.continue_on_failure:
                        logger.info(f"步骤失败且不继续执行，停止用例: {step.step_name}")
                        break

                self.db.flush()

            # 更新状态
            case_execution.status = "completed"
            case_execution.result = "pass" if case_execution.failed_steps == 0 else "fail"

            self.db.commit()
            self.db.refresh(case_execution)

        except Exception as e:
            logger.error(f"用例执行失败: {e}")
            case_execution.status = "failed"
            case_execution.result = "fail"
            case_execution.error_message = str(e)

            self.db.commit()
            self.db.refresh(case_execution)

        return case_execution

    def _load_scenarios(self, task: UITask) -> List[UIScenario]:
        """加载任务的所有场景"""
        scenario_ids = task.scenario_ids or []
        if not scenario_ids:
            return []

        # 转换字符串 ID 为 UUID 对象（SQLite + UUID 需要）
        valid_scenario_ids = []
        for sid in scenario_ids:
            if sid and isinstance(sid, (str, uuid.UUID)) and str(sid).strip():
                try:
                    if isinstance(sid, uuid.UUID):
                        valid_scenario_ids.append(sid)
                    else:
                        valid_scenario_ids.append(uuid.UUID(str(sid)))
                except ValueError:
                    logger.warning(f"跳过无效的 scenario_id UUID: {sid}")

        if not valid_scenario_ids:
            return []

        scenarios = self.db.query(UIScenario).filter(
            UIScenario.id.in_(valid_scenario_ids)
        ).order_by(UIScenario.execution_order).all()

        logger.info(f"加载了 {len(scenarios)} 个场景")
        return scenarios

    def _load_cases(self, scenario: UIScenario) -> List[UICase]:
        """加载场景的所有用例"""
        case_ids = scenario.case_ids or []
        if not case_ids:
            return []

        # 转换字符串 ID 为 UUID 对象（SQLite + UUID 需要）
        valid_case_ids = []
        for cid in case_ids:
            if cid and isinstance(cid, (str, uuid.UUID)) and str(cid).strip():
                try:
                    if isinstance(cid, uuid.UUID):
                        valid_case_ids.append(cid)
                    else:
                        valid_case_ids.append(uuid.UUID(str(cid)))
                except ValueError:
                    logger.warning(f"跳过无效的 case_id UUID: {cid}")

        if not valid_case_ids:
            return []

        cases = self.db.query(UICase).filter(
            UICase.id.in_(valid_case_ids)
        ).all()

        logger.info(f"加载了 {len(cases)} 个用例")
        return cases

    def _load_steps(self, case: UICase) -> List[UIStep]:
        """加载用例的所有步骤"""
        step_ids = case.step_ids or []
        if not step_ids:
            return []

        # 转换字符串 ID 为 UUID 对象（SQLite + UUID 需要）
        valid_step_ids = []
        for sid in step_ids:
            if sid and isinstance(sid, (str, uuid.UUID)) and str(sid).strip():
                try:
                    if isinstance(sid, uuid.UUID):
                        valid_step_ids.append(sid)
                    else:
                        valid_step_ids.append(uuid.UUID(str(sid)))
                except ValueError:
                    logger.warning(f"跳过无效的 step_id UUID: {sid}")

        if not valid_step_ids:
            return []

        steps = self.db.query(UIStep).filter(
            UIStep.id.in_(valid_step_ids)
        ).order_by(UIStep.step_order).all()

        logger.info(f"加载了 {len(steps)} 个步骤")
        return steps

    def _update_execution_stats(self, execution: TestExecution):
        """更新执行统计信息"""
        # 统计所有场景执行记录
        scenario_executions = self.db.query(ScenarioExecution).filter(
            ScenarioExecution.test_execution_id == execution.id
        ).all()

        execution.total_scenarios = len(scenario_executions)

        # 统计总数据
        execution.total_cases = sum(se.total_cases for se in scenario_executions)
        execution.total_steps = sum(se.total_steps for se in scenario_executions)
        execution.passed_steps = sum(se.passed_steps for se in scenario_executions)
        execution.failed_steps = sum(se.failed_steps for se in scenario_executions)

    def _update_scenario_stats(self, scenario_execution: ScenarioExecution):
        """更新场景统计信息"""
        # 统计所有用例执行记录
        case_executions = self.db.query(CaseExecution).filter(
            CaseExecution.scenario_execution_id == scenario_execution.id
        ).all()

        scenario_execution.total_cases = len(case_executions)
        scenario_execution.total_steps = sum(ce.total_steps for ce in case_executions)
        scenario_execution.passed_steps = sum(ce.passed_steps for ce in case_executions)
        scenario_execution.failed_steps = sum(ce.failed_steps for ce in case_executions)
