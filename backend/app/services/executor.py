"""
任务执行器

负责协调整个测试执行流程：
1. 加载任务、场景、用例、步骤
2. 按顺序执行步骤
3. 记录执行结果和日志
4. 处理失败和继续逻辑
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.ui_task import UITask, UIScenario, UICase, UIStep
from ..models.execution import TestExecution, ScenarioExecution, CaseExecution, StepExecution
from ..models.keyword import Keyword
from ..services.keyword_engine import KeywordEngine
from ..services.playwright_browser import PlaywrightBrowser
from ..schemas.execution import ExecutionRequest

logger = logging.getLogger(__name__)


class TaskExecutor:
    """任务执行器"""

    def __init__(self, db: Session):
        self.db = db
        self.keyword_engine = None
        self.browser_manager: Optional[PlaywrightBrowser] = None
        self.current_execution: Optional[TestExecution] = None

    async def execute_task(self, request: ExecutionRequest) -> TestExecution:
        """
        执行任务

        Args:
            request: 执行请求

        Returns:
            TestExecution: 执行记录
        """
        logger.info(f"Starting task execution: {request.task_id}")

        # 1. 加载任务
        task = self.db.query(UITask).filter(UITask.id == request.task_id).first()
        if not task:
            raise ValueError(f"Task not found: {request.task_id}")

        # 2. 创建执行记录
        execution = TestExecution(
            task_id=request.task_id,
            project_id=task.project_id,
            user_id=None,  # TODO: 从 token 获取
            status="running",
            started_at=datetime.now(timezone.utc),
            execution_config=request.execution_config or {},
            browser_config=request.browser_config or {},
            environment=request.environment
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        self.current_execution = execution

        try:
            # 3. 初始化浏览器
            browser_config = request.browser_config or {}

            # 自动尝试连接本地浏览器（如果未配置）
            # 优先级：1. 明确配置的 use_local/remote_url 2. 自动尝试本地浏览器 3. 容器内浏览器
            if not browser_config.get("use_local") and not browser_config.get("remote_url"):
                # 尝试自动检测并连接本地浏览器
                logger.info("尝试自动连接本地浏览器...")
                try:
                    test_browser = PlaywrightBrowser(config={"use_local": True, "headless": browser_config.get("headless", False)})
                    await test_browser.start_browser()
                    # 如果成功，使用这个配置
                    browser_config["use_local"] = True
                    browser_config["headless"] = browser_config.get("headless", False)
                    await test_browser.close()
                    logger.info("✓ 检测到本地浏览器可用，将使用本地浏览器")
                except Exception as e:
                    logger.info(f"本地浏览器不可用 ({e})，将使用容器内浏览器")
                    # 本地浏览器不可用，使用容器内浏览器
                    browser_config["use_local"] = False
                    browser_config["headless"] = browser_config.get("headless", True)

            self.browser_manager = PlaywrightBrowser(config=browser_config)
            await self.browser_manager.start_browser()
            self.keyword_engine = KeywordEngine(browser_manager=self.browser_manager)

            # 4. 加载场景
            scenarios = []
            for scenario_id in task.scenario_ids:
                scenario = self.db.query(UIScenario).filter(
                    and_(
                        UIScenario.id == scenario_id,
                        UIScenario.task_id == task.id
                    )
                ).first()
                if scenario:
                    scenarios.append(scenario)

            # 按执行顺序排序
            scenarios.sort(key=lambda s: s.execution_order)

            logger.info(f"Loaded {len(scenarios)} scenarios")

            total_steps = 0
            passed_steps = 0
            failed_steps = 0

            # 5. 执行每个场景
            for scenario in scenarios:
                scenario_result = await self._execute_scenario(execution, scenario)
                total_steps += scenario_result["total_steps"]
                passed_steps += scenario_result["passed_steps"]
                failed_steps += scenario_result["failed_steps"]

            # 6. 更新执行结果
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.total_scenarios = len(scenarios)
            execution.total_steps = total_steps
            execution.passed_steps = passed_steps
            execution.failed_steps = failed_steps

            if failed_steps == 0:
                execution.status = "completed"
                execution.result = "pass"
            else:
                execution.status = "completed"
                execution.result = "fail" if passed_steps == 0 else "partial"

            self.db.commit()
            self.db.refresh(execution)

            logger.info(f"Task execution completed: {execution.result}")

        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            execution.status = "failed"
            execution.result = "error"
            execution.error_message = str(e)
            execution.completed_at = datetime.now(timezone.utc)

            if execution.started_at:
                execution.duration = (execution.completed_at - execution.started_at).total_seconds()

            self.db.commit()
            self.db.refresh(execution)

        finally:
            # 7. 清理浏览器
            if self.browser_manager:
                await self.browser_manager.close()

        return execution

    async def _execute_scenario(
        self,
        task_execution: TestExecution,
        scenario: UIScenario
    ) -> Dict[str, int]:
        """执行场景"""
        logger.info(f"Executing scenario: {scenario.name}")

        # 创建场景执行记录
        scenario_execution = ScenarioExecution(
            test_execution_id=task_execution.id,
            scenario_id=scenario.id,
            status="running",
            started_at=datetime.now(timezone.utc),
            execution_order=scenario.execution_order
        )
        self.db.add(scenario_execution)
        self.db.commit()
        self.db.refresh(scenario_execution)

        try:
            # 加载用例
            cases = []
            for case_id in scenario.case_ids:
                case = self.db.query(UICase).filter(
                    and_(
                        UICase.id == case_id,
                        UICase.scenario_id == scenario.id
                    )
                ).first()
                if case:
                    cases.append(case)

            logger.info(f"Loaded {len(cases)} cases for scenario")

            total_steps = 0
            passed_steps = 0
            failed_steps = 0

            # 执行每个用例
            for case in cases:
                case_result = await self._execute_case(scenario_execution, case)
                total_steps += case_result["total_steps"]
                passed_steps += case_result["passed_steps"]
                failed_steps += case_result["failed_steps"]

            # 更新场景执行结果
            scenario_execution.completed_at = datetime.now(timezone.utc)
            scenario_execution.duration = (scenario_execution.completed_at - scenario_execution.started_at).total_seconds()
            scenario_execution.total_cases = len(cases)
            scenario_execution.total_steps = total_steps
            scenario_execution.passed_steps = passed_steps
            scenario_execution.failed_steps = failed_steps

            if failed_steps == 0:
                scenario_execution.status = "completed"
                scenario_execution.result = "pass"
            else:
                scenario_execution.status = "completed"
                scenario_execution.result = "fail" if passed_steps == 0 else "partial"

            self.db.commit()

            return {
                "total_steps": total_steps,
                "passed_steps": passed_steps,
                "failed_steps": failed_steps
            }

        except Exception as e:
            logger.error(f"Scenario execution failed: {e}", exc_info=True)
            scenario_execution.status = "failed"
            scenario_execution.result = "error"
            scenario_execution.error_message = str(e)
            scenario_execution.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            raise

    async def _execute_case(
        self,
        scenario_execution: ScenarioExecution,
        case: UICase
    ) -> Dict[str, int]:
        """执行用例"""
        logger.info(f"Executing case: {case.name}")

        # 创建用例执行记录
        case_execution = CaseExecution(
            scenario_execution_id=scenario_execution.id,
            case_id=case.id,
            status="running",
            started_at=datetime.now(timezone.utc),
            priority=case.priority
        )
        self.db.add(case_execution)
        self.db.commit()
        self.db.refresh(case_execution)

        try:
            # 加载步骤
            steps = []
            for step_id in case.step_ids:
                step = self.db.query(UIStep).filter(
                    and_(
                        UIStep.id == step_id,
                        UIStep.case_id == case.id
                    )
                ).first()
                if step:
                    steps.append(step)

            # 按顺序排序
            steps.sort(key=lambda s: s.step_order)

            logger.info(f"Loaded {len(steps)} steps for case")

            total_steps = 0
            passed_steps = 0
            failed_steps = 0

            # 执行每个步骤
            for step in steps:
                if not step.enabled:
                    logger.info(f"Step {step.step_name} is disabled, skipping")
                    continue

                step_result = await self._execute_step(case_execution, step)
                total_steps += 1

                if step_result["result"] == "pass":
                    passed_steps += 1
                elif step_result["result"] == "fail":
                    failed_steps += 1

                    # 如果不继续失败，停止执行
                    if not step.continue_on_failure:
                        logger.warning(f"Step failed and continue_on_failure=False, stopping case execution")
                        break

            # 更新用例执行结果
            case_execution.completed_at = datetime.now(timezone.utc)
            case_execution.duration = (case_execution.completed_at - case_execution.started_at).total_seconds()
            case_execution.total_steps = total_steps
            case_execution.passed_steps = passed_steps
            case_execution.failed_steps = failed_steps

            if failed_steps == 0:
                case_execution.status = "completed"
                case_execution.result = "pass"
            else:
                case_execution.status = "completed"
                case_execution.result = "fail" if passed_steps == 0 else "partial"

            self.db.commit()

            return {
                "total_steps": total_steps,
                "passed_steps": passed_steps,
                "failed_steps": failed_steps
            }

        except Exception as e:
            logger.error(f"Case execution failed: {e}", exc_info=True)
            case_execution.status = "failed"
            case_execution.result = "error"
            case_execution.error_message = str(e)
            case_execution.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            raise

    async def _execute_step(
        self,
        case_execution: CaseExecution,
        step: UIStep
    ) -> Dict[str, Any]:
        """执行单个步骤"""
        logger.info(f"Executing step: {step.step_name}")

        # 创建步骤执行记录
        step_execution = StepExecution(
            case_execution_id=case_execution.id,
            step_id=step.id,
            keyword_id=step.keyword_id,
            status="running",
            started_at=datetime.now(timezone.utc),
            step_name=step.step_name,
            step_order=step.step_order,
            keyword_name="",
            category=step.step_type,
            parameters=step.parameters,
            continue_on_failure=step.continue_on_failure,
            logs=[]
        )
        self.db.add(step_execution)
        self.db.commit()
        self.db.refresh(step_execution)

        try:
            # 获取关键字
            keyword = self.db.query(Keyword).filter(Keyword.id == step.keyword_id).first()
            if not keyword:
                raise ValueError(f"Keyword not found: {step.keyword_id}")

            step_execution.keyword_name = keyword.name
            step_execution.category = keyword.category

            # 执行关键字
            result = await self.keyword_engine.execute(
                keyword_def=keyword,
                parameters=step.parameters,
                context={}
            )

            # 更新执行结果
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration = (step_execution.completed_at - step_execution.started_at).total_seconds()
            step_execution.status = "completed"
            step_execution.result = "pass" if result.get("success") else "fail"
            step_execution.output = result

            # 添加日志
            logs = result.get("logs", [])
            if logs:
                step_execution.logs = [{"timestamp": datetime.now(timezone.utc).isoformat(), "level": "info", "message": log} for log in logs]

            self.db.commit()

            return {
                "result": step_execution.result,
                "duration": step_execution.duration,
                "output": result
            }

        except Exception as e:
            logger.error(f"Step execution failed: {e}", exc_info=True)

            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration = (step_execution.completed_at - step_execution.started_at).total_seconds()
            step_execution.status = "completed"
            step_execution.result = "fail"
            step_execution.error_message = str(e)

            # 失败时截图
            try:
                screenshot_path = await self.browser_manager.take_screenshot()
                step_execution.screenshot_path = screenshot_path
                logger.info(f"Screenshot saved: {screenshot_path}")
            except Exception as screenshot_error:
                logger.warning(f"Failed to take screenshot: {screenshot_error}")

            self.db.commit()

            return {
                "result": "fail",
                "error": str(e)
            }
