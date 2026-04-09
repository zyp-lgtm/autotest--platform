"""
任务执行器

负责协调整个测试执行流程：
1. 加载任务、场景、用例、步骤
2. 按顺序执行步骤
3. 记录执行结果和日志
4. 处理失败和继续逻辑
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.ui_task import UITask, UIScenario, UICase, UIStep
from ..models.execution import TestExecution, ScenarioExecution, CaseExecution, StepExecution
from ..models.keyword import Keyword
from ..services.keyword_engine import KeywordEngine
from ..services.playwright_browser import PlaywrightBrowser
from ..services.debug_collector import DebugInfoCollector
from ..services.error_classifier import ErrorClassifier
from ..schemas.execution import ExecutionRequest
from ..api import agent as agent_manager

logger = logging.getLogger(__name__)


def _ensure_datetime_aware(dt):
    """确保 datetime 对象带有时区信息（SQLite 兼容）"""
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class TaskExecutor:
    """任务执行器"""

    def __init__(self, db: Session):
        self.db = db
        self.keyword_engine = None
        self.browser_manager: Optional[PlaywrightBrowser] = None
        self.current_execution: Optional[TestExecution] = None
        self.debug_collector = DebugInfoCollector()  # 调试信息收集器

    async def _setup_debug_collector(self) -> None:
        """设置调试信息收集器"""
        try:
            # 启动调试会话
            session_id = str(self.current_execution.id)
            self.debug_collector.start_session(session_id)
            logger.info(f"✅ 已启动调试会话: {session_id}")

            # 设置页面监听器
            if self.browser_manager:
                page = await self.browser_manager.get_page()
                await self.debug_collector.setup_page_listeners(page)
                logger.info("✅ 已设置页面监听器: 控制台 + 网络")

        except Exception as e:
            logger.error(f"设置调试收集器失败: {e}")
            # 不阻断执行，只是日志记录

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
            # 3. 获取浏览器配置
            browser_config = request.browser_config or {}

            # 4. 检查是否有可用的本地 Agent
            available_agents = agent_manager.manager.get_all_agents()
            logger.info(f"当前可用 Agent 数量: {len(available_agents)}")
            logger.info(f"browser_config: {browser_config}")
            logger.info(f"use_agent 配置: {browser_config.get('use_agent', True)}")

            if available_agents and browser_config.get("use_agent", True):
                # 使用本地 Agent 执行
                execution.execution_mode = "agent"
                self.db.flush()
                logger.info(f"发现 {len(available_agents)} 个可用 Agent，使用 Agent 执行任务")

                # 获取第一个可用的 Agent
                agent_id = list(available_agents.keys())[0]
                logger.info(f"使用 Agent: {agent_id}")

                # Agent 执行时默认显示浏览器（除非明确要求 headless）
                agent_browser_config = browser_config.copy()
                if "headless" not in agent_browser_config:
                    agent_browser_config["headless"] = False
                    logger.info("Agent 执行模式：显示浏览器")

                # 转换任务为 Agent 格式并下发
                result = await self._execute_via_agent(agent_id, task, agent_browser_config)

                # 更新执行结果
                execution.completed_at = datetime.now(timezone.utc)
                started_at_aware = _ensure_datetime_aware(execution.started_at)
                execution.duration = (execution.completed_at - started_at_aware).total_seconds()

                if result.get("success"):
                    execution.status = "completed"
                    execution.result = "pass"
                    execution.total_steps = result.get("total_steps", 0)
                    execution.passed_steps = result.get("passed_steps", 0)
                    execution.failed_steps = result.get("failed_steps", 0)
                else:
                    execution.status = "completed"
                    execution.result = "fail"
                    execution.error_message = result.get("error", "Agent 执行失败")
                    execution.total_steps = result.get("total_steps", 0)
                    execution.passed_steps = result.get("passed_steps", 0)
                    execution.failed_steps = result.get("failed_steps", 0)

                self.db.commit()
                self.db.refresh(execution)

                return execution

            # 5. 没有 Agent 或不使用 Agent，在容器内执行
            execution.execution_mode = "direct"
            self.db.flush()
            logger.info("在容器内执行任务")

            # 自动尝试连接本地浏览器（如果未配置）
            # 优先级：1. 明确配置的 use_local/remote_url 2. 自动尝试本地浏览器 3. 容器内浏览器
            if not browser_config.get("use_local") and not browser_config.get("remote_url"):
                # 尝试自动检测并连接本地浏览器
                logger.info("尝试自动连接本地浏览器...")
                try:
                    # 直接尝试创建并连接本地浏览器
                    self.browser_manager = PlaywrightBrowser(config={
                        "use_local": True,
                        "headless": browser_config.get("headless", False)
                    })
                    await self.browser_manager.start_browser()
                    logger.info("✓ 检测到本地浏览器可用，将使用本地浏览器")

                    # 设置调试收集器
                    await self._setup_debug_collector()
                except Exception as e:
                    logger.info(f"本地浏览器不可用 ({e})，将使用容器内浏览器")
                    # 本地浏览器不可用，创建容器内浏览器
                    self.browser_manager = PlaywrightBrowser(config={
                        "browser_type": browser_config.get("browser_type", "chromium"),
                        "headless": browser_config.get("headless", True),
                        "use_local": False
                    })
                    await self.browser_manager.start_browser()

                    # 设置调试收集器
                    await self._setup_debug_collector()
            else:
                # 使用用户提供的配置
                self.browser_manager = PlaywrightBrowser(config=browser_config)
                await self.browser_manager.start_browser()

                # 设置调试收集器
                await self._setup_debug_collector()

            self.keyword_engine = KeywordEngine(browser_manager=self.browser_manager)

            # 4. 加载场景（优化：使用 IN 子句避免 N+1 查询）
            scenario_id_uuids = []
            for scenario_id in task.scenario_ids:
                scenario_id_uuid = uuid.UUID(scenario_id) if isinstance(scenario_id, str) else scenario_id
                scenario_id_uuids.append(scenario_id_uuid)

            scenarios = self.db.query(UIScenario).filter(
                and_(
                    UIScenario.id.in_(scenario_id_uuids),
                    UIScenario.task_id == task.id
                )
            ).all()

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
            started_at_aware = _ensure_datetime_aware(execution.started_at)
            execution.duration = (execution.completed_at - started_at_aware).total_seconds()
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
                started_at_aware = _ensure_datetime_aware(execution.started_at)
                execution.duration = (execution.completed_at - started_at_aware).total_seconds()

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
            # 加载用例（优化：使用 IN 子句避免 N+1 查询）
            # 处理 case_ids（可能是 JSON 字符串或列表）
            case_ids_list = scenario.case_ids
            if isinstance(case_ids_list, str):
                try:
                    case_ids_list = json.loads(case_ids_list)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse case_ids JSON: {e}, using empty list")
                    case_ids_list = []

            case_id_uuids = []
            for case_id in case_ids_list:
                case_id_uuid = uuid.UUID(case_id) if isinstance(case_id, str) else case_id
                case_id_uuids.append(case_id_uuid)

            cases = self.db.query(UICase).filter(
                and_(
                    UICase.id.in_(case_id_uuids),
                    UICase.scenario_id == scenario.id
                )
            ).all()

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
            started_at_aware = _ensure_datetime_aware(scenario_execution.started_at)
            scenario_execution.duration = (scenario_execution.completed_at - started_at_aware).total_seconds()
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

        case_execution = None  # 初始化变量

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

            # 处理 step_ids（可能是 JSON 字符串或列表）
            step_ids_list = case.step_ids
            if isinstance(step_ids_list, str):
                try:
                    step_ids_list = json.loads(step_ids_list)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse step_ids JSON: {e}, using empty list")
                    step_ids_list = []

            for step_id in step_ids_list:
                # 将字符串 ID 转换为 UUID 对象
                step_id_uuid = uuid.UUID(step_id) if isinstance(step_id, str) else step_id
                step = self.db.query(UIStep).filter(
                    and_(
                        UIStep.id == step_id_uuid,
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
            started_at_aware = _ensure_datetime_aware(case_execution.started_at)
            case_execution.duration = (case_execution.completed_at - started_at_aware).total_seconds()
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
            # 只有在 case_execution 成功创建并提交后才更新其状态
            if case_execution is not None:
                try:
                    case_execution.status = "failed"
                    case_execution.result = "error"
                    case_execution.error_message = str(e)
                    case_execution.completed_at = datetime.now(timezone.utc)
                    self.db.commit()
                except Exception as commit_error:
                    logger.error(f"Failed to update case_execution status: {commit_error}")
            raise

    async def _execute_step(
        self,
        case_execution: CaseExecution,
        step: UIStep,
        step_execution: StepExecution = None,
        is_retry: bool = False
    ) -> Dict[str, Any]:
        """执行单个步骤（集成调试信息收集）"""
        import time
        start_time = time.time()

        logger.info(f"Executing step: {step.step_name}")

        # 记录步骤开始（调试收集器）
        self.debug_collector.log_step_start(
            step_name=step.step_name,
            keyword=step.keyword_id,
            parameters=step.parameters or {}
        )

        # 创建步骤执行记录（如果不是重试的话）
        if step_execution is None:
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
                retry_attempt=0,
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

            # 记录开始执行日志（详细）
            execution_logs = []
            execution_logs.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "info",
                "message": f"开始执行步骤: {step.step_name}"
            })
            execution_logs.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "debug",
                "message": f"关键字: {keyword.name} ({keyword.category})"
            })
            execution_logs.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "debug",
                "message": f"关键字ID: {step.keyword_id}"
            })

            # 记录参数日志（详细）
            if step.parameters:
                execution_logs.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "info",
                    "message": f"参数: {json.dumps(step.parameters, ensure_ascii=False)}"
                })
                # 记录每个参数的解析
                for param_name, param_value in (step.parameters or {}).items():
                    self.debug_collector.log_parameter_resolution(
                        param_name=param_name,
                        raw_value=str(param_value),
                        resolved_value=param_value
                    )

            # 执行关键字
            result = await self.keyword_engine.execute(
                keyword_def=keyword,
                parameters=step.parameters or {},
                context={}
            )

            # 记录执行结果日志（详细）
            duration = time.time() - start_time

            if result.get("success"):
                execution_logs.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "info",
                    "message": f"✓ 步骤执行成功: {step.step_name} (耗时: {duration:.2f}s)"
                })
                execution_logs.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "debug",
                    "message": f"返回值: {json.dumps(result, ensure_ascii=False)}"
                })
            else:
                error_msg = result.get('error', '未知错误')
                execution_logs.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "error",
                    "message": f"✗ 步骤执行失败: {error_msg}"
                })

                # 记录详细的错误堆栈
                if "traceback" in result:
                    execution_logs.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "level": "error",
                        "message": f"错误堆栈: {result['traceback']}"
                    })

            # 添加关键字引擎返回的日志
            if "logs" in result:
                for log in result["logs"]:
                    execution_logs.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "level": "info",
                        "message": str(log)
                    })

            # 更新执行结果
            step_execution.completed_at = datetime.now(timezone.utc)
            started_at_aware = _ensure_datetime_aware(step_execution.started_at)
            step_execution.duration = (step_execution.completed_at - started_at_aware).total_seconds()
            step_execution.status = "completed"
            step_execution.result = "pass" if result.get("success") else "fail"
            step_execution.output = result
            step_execution.logs = execution_logs

            # 设置错误消息（如果失败）
            if not result.get("success"):
                error_msg = result.get('error') or result.get('message', '未知错误')
                step_execution.error_message = error_msg

                # 使用错误分类器丰富错误信息
                error_info = ErrorClassifier.enrich_error_info(error_msg)
                logger.info(f"步骤失败: {error_msg}")
                logger.info(f"错误分类: {error_info['category']}, 严重程度: {error_info['severity']}")

                # 将错误分类信息添加到output中
                if not step_execution.output:
                    step_execution.output = {}
                step_execution.output['error_category'] = error_info['category']
                step_execution.output['error_severity'] = error_info['severity']
                step_execution.output['error_suggestion'] = error_info['suggestion']

                # 在日志中记录错误建议
                suggestion = error_info['suggestion']
                execution_logs.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "info",
                    "message": f"💡 建议: {suggestion['title']} - {suggestion['description']}"
                })
                for solution in suggestion['solutions'][:2]:  # 只显示前2个建议
                    execution_logs.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "level": "info",
                        "message": f"   • {solution}"
                    })

                # 强制刷新到数据库
                self.db.flush()

                # 检查是否应该重试
                should_retry = self._should_retry_step(step, error_msg, step_execution.retry_attempt)

                if should_retry:
                    # 执行重试
                    retry_attempt = step_execution.retry_attempt + 1
                    max_retries = step.execution_config.get('max_retries', 3) if step.execution_config else 3

                    logger.info(f"步骤失败，执行第 {retry_attempt}/{max_retries} 次重试")

                    # 创建重试记录
                    retry_step_execution = StepExecution(
                        case_execution_id=step_execution.case_execution_id,
                        step_id=step.step_id,
                        keyword_id=step.keyword_id,
                        status="running",
                        started_at=datetime.now(timezone.utc),
                        step_name=step.step_name,
                        step_order=step.step_order,
                        keyword_name=step_execution.keyword_name,
                        category=step_execution.category,
                        parameters=step.parameters,
                        continue_on_failure=step.continue_on_failure,
                        retry_attempt=retry_attempt,
                        retry_of=step_execution.id,
                        logs=[]
                    )
                    self.db.add(retry_step_execution)
                    self.db.commit()

                    # 递归调用自己执行重试
                    return await self._execute_step(case_execution, step, retry_step_execution, is_retry=True)

                # 记录失败不需要重试或重试次数已用尽
                if step_execution.retry_attempt > 0:
                    logger.info(f"步骤在 {step_execution.retry_attempt} 次尝试后仍然失败，放弃重试")

            # 记录步骤完成（调试收集器）
            self.debug_collector.log_step_complete(
                step_name=step.step_name,
                result=result,
                duration=duration
            )

            self.db.commit()

            return {
                "result": step_execution.result,
                "duration": step_execution.duration,
                "output": result
            }

        except Exception as e:
            logger.error(f"Step execution failed: {e}", exc_info=True)

            # 捕获失败时的调试信息
            if self.browser_manager:
                try:
                    page = await self.browser_manager.get_page()

                    # 捕获完整的调试信息
                    debug_info = await self.debug_collector.capture_failure_info(
                        page=page,
                        step_name=step.step_name,
                        error=str(e),
                        selector=step.parameters.get("selector") if step.parameters else None
                    )

                    # 更新执行记录
                    step_execution.screenshot_path = debug_info.get("screenshot")
                    # 将 debug_info 转换为 JSON 字符串以便存储
                    step_execution.debug_info = json.dumps(debug_info, ensure_ascii=False)

                    logger.info(f"已捕获失败调试信息: {debug_info.get('report_path')}")
                except Exception as debug_error:
                    logger.error(f"捕获调试信息失败: {debug_error}")

            step_execution.completed_at = datetime.now(timezone.utc)
            started_at_aware = _ensure_datetime_aware(step_execution.started_at)
            step_execution.duration = (step_execution.completed_at - started_at_aware).total_seconds()
            step_execution.status = "completed"
            step_execution.result = "fail"
            step_execution.error_message = str(e)

            # 使用错误分类器丰富异常信息
            error_info = ErrorClassifier.enrich_error_info(str(e))
            logger.info(f"异常分类: {error_info['category']}, 严重程度: {error_info['severity']}")

            # 将错误分类信息添加到output中
            if not step_execution.output:
                step_execution.output = {}
            step_execution.output['error_category'] = error_info['category']
            step_execution.output['error_severity'] = error_info['severity']
            step_execution.output['error_suggestion'] = error_info['suggestion']

            # 在日志中记录错误建议
            suggestion = error_info['suggestion']
            logger.info(f"💡 异常建议: {suggestion['title']} - {suggestion['description']}")

            # 失败时尝试截图（备用方案）
            if not step_execution.screenshot_path:
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

    async def _execute_via_agent(self, agent_id: str, task: UITask, browser_config: dict) -> Dict[str, Any]:
        """
        通过本地 Agent 执行任务（带完整日志记录）

        Args:
            agent_id: Agent ID
            task: 任务对象
            browser_config: 浏览器配置

        Returns:
            执行结果
        """
        logger.info(f"通过 Agent {agent_id} 执行任务 {task.id}")
        logger.info(f"浏览器配置: {browser_config}")

        # 加载场景和步骤，同时创建执行记录（优化：使用 IN 子句避免 N+1 查询）
        total_steps = 0
        passed_steps = 0
        failed_steps = 0
        all_step_results = []

        scenario_id_uuids = []
        for scenario_id in task.scenario_ids:
            scenario_id_uuid = uuid.UUID(scenario_id) if isinstance(scenario_id, str) else scenario_id
            scenario_id_uuids.append(scenario_id_uuid)

        scenarios = self.db.query(UIScenario).filter(
            and_(
                UIScenario.id.in_(scenario_id_uuids),
                UIScenario.task_id == task.id
            )
        ).all()

        for scenario in scenarios:

            # 创建场景执行记录
            scenario_execution = ScenarioExecution(
                test_execution_id=self.current_execution.id,
                scenario_id=scenario.id,
                status="running",
                started_at=datetime.now(timezone.utc),
                execution_order=scenario.execution_order
            )
            self.db.add(scenario_execution)
            self.db.commit()
            self.db.refresh(scenario_execution)

            # 处理 case_ids（可能是 JSON 字符串或列表）
            case_ids_list = scenario.case_ids
            if isinstance(case_ids_list, str):
                try:
                    case_ids_list = json.loads(case_ids_list)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse case_ids JSON: {e}, using empty list")
                    case_ids_list = []

            # 优化：使用 IN 子句避免 N+1 查询
            case_id_uuids = []
            for case_id in case_ids_list:
                case_id_uuid = uuid.UUID(case_id) if isinstance(case_id, str) else case_id
                case_id_uuids.append(case_id_uuid)

            cases = self.db.query(UICase).filter(
                and_(
                    UICase.id.in_(case_id_uuids),
                    UICase.scenario_id == scenario.id
                )
            ).all()

            for case in cases:

                # 创建用例执行记录
                case_execution = CaseExecution(
                    scenario_execution_id=scenario_execution.id,
                    case_id=case.id,
                    status="running",
                    started_at=datetime.now(timezone.utc)
                )
                self.db.add(case_execution)
                self.db.commit()
                self.db.refresh(case_execution)

                # 收集步骤并转换为 Agent 格式
                agent_steps = []
                step_mappings = []  # 保存步骤ID映射

                # 处理 step_ids（可能是 JSON 字符串或列表）
                step_ids_list = case.step_ids
                if isinstance(step_ids_list, str):
                    try:
                        step_ids_list = json.loads(step_ids_list)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse step_ids JSON: {e}, using empty list")
                        step_ids_list = []

                for step_id in step_ids_list:
                    # 将字符串 ID 转换为 UUID 对象
                    step_id_uuid = uuid.UUID(step_id) if isinstance(step_id, str) else step_id
                    step = self.db.query(UIStep).filter(
                        and_(UIStep.id == step_id_uuid, UIStep.case_id == case.id)
                    ).first()

                    if not step or not step.enabled:
                        continue

                    # 获取关键字
                    keyword = self.db.query(Keyword).filter(Keyword.id == step.keyword_id).first()
                    if not keyword:
                        continue

                    # 转换为 Agent 步骤格式
                    agent_step = self._convert_step_to_agent_format(keyword, step.parameters)
                    if agent_step:
                        agent_steps.append(agent_step)
                        step_mappings.append({
                            "step_id": step.id,
                            "step_name": step.step_name,
                            "keyword_name": keyword.name,
                            "keyword_id": keyword.id,
                            "parameters": step.parameters,
                            "step_order": step.step_order
                        })
                        total_steps += 1

                # 下发任务给 Agent
                task_message = {
                    "type": "task",
                    "task_id": str(task.id),
                    "browser_type": browser_config.get("browser_type", "chromium"),
                    "headless": browser_config.get("headless", False),
                    "steps": agent_steps
                }

                logger.info(f"下发 {len(agent_steps)} 个步骤到 Agent")
                success = await agent_manager.manager.send_to_agent(agent_id, task_message)

                if not success:
                    # 记录失败
                    for mapping in step_mappings:
                        self._create_step_execution_record(
                            case_execution.id,
                            mapping,
                            mapping["keyword_id"],
                            "failed",
                            error="发送任务到 Agent 失败"
                        )
                    failed_steps += len(step_mappings)
                    continue

                # 等待 Agent 执行完成
                logger.info("等待 Agent 执行完成...")
                task_result_data = await agent_manager.manager.wait_for_task_result(str(task.id), timeout=60.0)

                # 清理任务结果缓存
                agent_manager.manager.clear_task_result(str(task.id))

                # 处理 Agent 返回的结果
                agent_results = []
                if task_result_data and task_result_data.get("result"):
                    agent_result = task_result_data["result"]
                    if "results" in agent_result:
                        agent_results = agent_result["results"]
                        logger.info(f"收到 Agent 执行结果: {len(agent_results)} 个步骤")

                # 根据实际结果创建执行记录
                for i, mapping in enumerate(step_mappings):
                    # 获取对应步骤的执行结果
                    step_agent_result = agent_results[i] if i < len(agent_results) else {}

                    if step_agent_result.get("success"):
                        step_result = "pass"
                        status = "completed"

                        # 构建详细日志
                        logs = [{
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "level": "info",
                            "message": f"开始执行步骤: {mapping['step_name']} (关键字: {mapping['keyword_name']})"
                        }]

                        # 添加参数日志
                        if mapping.get("parameters"):
                            params_str = ", ".join([f"{k}={v}" for k, v in mapping["parameters"].items()])
                            logs.append({
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "level": "info",
                                "message": f"参数: {params_str}"
                            })

                        # 添加成功完成日志
                        logs.append({
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "level": "info",
                            "message": f"✓ 步骤执行成功: {mapping['step_name']}"
                        })

                        # 如果有截图路径，添加到日志中
                        if step_agent_result.get("screenshot"):
                            logs.append({
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "level": "info",
                                "message": f"截图已保存: {step_agent_result['screenshot']}"
                            })
                    else:
                        step_result = "fail"
                        status = "failed"

                        error_msg = step_agent_result.get("error", "未知错误")

                        logs = [{
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "level": "error",
                            "message": f"步骤执行失败: {mapping['step_name']} - {error_msg}"
                        }]

                    self._create_step_execution_record(
                        case_execution.id,
                        mapping,
                        mapping["keyword_id"],
                        status,
                        result=step_result,
                        logs=logs,
                        error=step_agent_result.get("error") if not step_agent_result.get("success") else None
                    )

                    if step_result == "pass":
                        passed_steps += 1
                    else:
                        failed_steps += 1

                # 更新用例执行结果
                case_execution.completed_at = datetime.now(timezone.utc)
                started_at_aware = _ensure_datetime_aware(case_execution.started_at)
                case_execution.duration = (case_execution.completed_at - started_at_aware).total_seconds()
                case_execution.total_steps = len(step_mappings)
                case_execution.passed_steps = passed_steps
                case_execution.failed_steps = failed_steps
                case_execution.status = "completed"
                case_execution.result = "pass" if failed_steps == 0 else "fail"
                self.db.commit()
                            # 更新场景执行结果
            scenario_execution.completed_at = datetime.now(timezone.utc)
            started_at_aware = _ensure_datetime_aware(scenario_execution.started_at)
            scenario_execution.duration = (scenario_execution.completed_at - started_at_aware).total_seconds()
            scenario_execution.total_cases = 1
            scenario_execution.total_steps = total_steps
            scenario_execution.passed_steps = passed_steps
            scenario_execution.failed_steps = failed_steps
            scenario_execution.status = "completed"
            scenario_execution.result = "pass" if failed_steps == 0 else "fail"
            self.db.commit()
        return {
            "success": True,
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "failed_steps": failed_steps
        }

    def _should_retry_step(
        self,
        step: UIStep,
        error_msg: str,
        current_attempt: int
    ) -> bool:
        """判断步骤是否应该重试

        Args:
            step: 步骤定义
            error_msg: 错误消息
            current_attempt: 当前尝试次数

        Returns:
            bool: True表示应该重试
        """
        # 检查步骤配置是否允许重试
        if step.execution_config and not step.execution_config.get('retry_on_failure', True):
            return False

        # 检查最大重试次数
        max_retries = step.execution_config.get('max_retries', 3) if step.execution_config else 3

        if current_attempt >= max_retries:
            return False

        # 检查错误类型是否可以重试
        # 可以重试的错误：超时、连接失败、临时网络问题
        # 不应重试的错误：断言失败、元素不存在（非超时原因）、脚本错误

        retryable_errors = [
            'timeout',
            '超时',
            'Timeout',
            'network',
            'network error',
            'connection',
            'connection refused',
            'Temporary',
            'temporary'
        ]

        # 检查错误消息是否包含可重试的关键词
        should_retry = any(keyword in error_msg for keyword in retryable_errors)

        # 特殊情况：元素找不到如果是超时导致的，可以重试
        if not should_retry and 'Timeout' in error_msg:
            should_retry = True

        return should_retry

    def _create_step_execution_record(
        self,
        case_execution_id: uuid.UUID,
        step_mapping: dict,
        keyword_id: uuid.UUID,
        status: str,
        result: str = None,
        error: str = None,
        logs: list = None
    ):
        """创建步骤执行记录"""
        step_execution = StepExecution(
            case_execution_id=case_execution_id,
            step_id=step_mapping["step_id"],
            keyword_id=keyword_id,  # 使用实际的 keyword_id
            status=status,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            duration=0,
            step_name=step_mapping["step_name"],
            step_order=step_mapping["step_order"],
            keyword_name=step_mapping["keyword_name"],
            category="UI",
            parameters=step_mapping["parameters"],
            continue_on_failure=False,
            logs=logs or [],
            error_message=error,
            result=result or ("pass" if status == "completed" and not error else "fail")
        )
        self.db.add(step_execution)
        self.db.flush()  # 先 flush 确保 error_message 保存
        self.db.commit()

    def _convert_step_to_agent_format(self, keyword: Keyword, parameters: dict) -> Optional[dict]:
        """
        将关键字步骤转换为 Agent 格式

        Args:
            keyword: 关键字对象
            parameters: 参数

        Returns:
            Agent 格式的步骤，如果不支持则返回 None
        """
        keyword_name = keyword.name

        # 映射关键字到 Agent 操作
        keyword_mapping = {
            "NAVIGATE": "navigate",
            "CLICK": "click",
            "INPUT": "input",
            "WAIT_FOR_ELEMENT": "wait",
            "SCREENSHOT": "screenshot"
        }

        agent_action = keyword_mapping.get(keyword_name)

        if not agent_action:
            logger.warning(f"关键字 {keyword_name} 在 Agent 中不支持")
            return None

        return {
            "action": agent_action,
            "parameters": parameters
        }
