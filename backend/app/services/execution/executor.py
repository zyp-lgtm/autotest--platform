"""
任务执行器（重构版）

协调器模式：负责任务执行的高级协调
- Agent 执行协调
- 直接执行协调（委托给 TaskOrchestrator）
- 浏览器生命周期管理
- 调试信息收集
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ...models.ui_task import UITask, UIScenario, UICase, UIStep
from ...models.execution import TestExecution, ScenarioExecution, CaseExecution, StepExecution
from ...models.keyword import Keyword
from ...services.playwright_browser import PlaywrightBrowser
from ...services.debug_collector import DebugInfoCollector
from ...services.keyword_engine import KeywordEngine
from ...schemas.execution import ExecutionRequest
from ...api import agent as agent_manager
from .task_orchestrator import TaskOrchestrator
from .step_executor import StepExecutor
from ...core.interfaces import (
    IKeywordEngine,
    IBrowserManager,
    IDebugCollector,
    IStepExecutor,
    ITaskOrchestrator
)

logger = logging.getLogger(__name__)


def _ensure_datetime_aware(dt):
    """确保 datetime 对象带有时区信息（SQLite 兼容）"""
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class TaskExecutor:
    """
    任务执行器（协调器模式）

    职责：
    1. 协调 Agent 执行和直接执行
    2. 管理浏览器生命周期
    3. 设置调试信息收集
    4. 委托具体执行给 TaskOrchestrator
    """

    def __init__(self, db: Session):
        """
        初始化任务执行器

        Args:
            db: 数据库会话
        """
        self.db = db
        # 使用接口类型注解，解耦具体实现
        self.browser_manager: Optional[IBrowserManager] = None
        self.keyword_engine: Optional[IKeywordEngine] = None
        self.current_execution: Optional[TestExecution] = None
        self.debug_collector: IDebugCollector = DebugInfoCollector()

        # 延迟初始化的组件（使用接口）
        self.step_executor: Optional[IStepExecutor] = None
        self.task_orchestrator: Optional[ITaskOrchestrator] = None

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

    def _initialize_orchestrator(self):
        """初始化执行编排器（延迟初始化）"""
        if not self.step_executor:
            self.step_executor = StepExecutor(
                db=self.db,
                keyword_engine=self.keyword_engine,
                browser_manager=self.browser_manager,
                debug_collector=self.debug_collector
            )

        if not self.task_orchestrator:
            self.task_orchestrator = TaskOrchestrator(
                db=self.db,
                step_executor=self.step_executor
            )

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
            # 直接访问 ConnectionManager 单例，避免 HTTP 认证问题
            logger.info("[DEBUG] 直接访问 ConnectionManager 单例查询 Agent...")
            from app.api.agent import manager as agent_mgr
            available_agents = agent_mgr.get_all_agents()

            logger.info(f"[DEBUG] 查询完成，available_agents 类型: {type(available_agents)}")
            logger.info(f"[DEBUG] available_agents 是否为 None: {available_agents is None}")
            logger.info(f"[DEBUG] available_agents 长度: {len(available_agents) if available_agents else 0}")
            if available_agents:
                logger.info(f"[DEBUG] Agent IDs: {list(available_agents.keys())}")
            logger.info(f"当前可用 Agent 数量: {len(available_agents)}")
            logger.info(f"browser_config: {browser_config}")
            logger.info(f"use_agent 配置: {browser_config.get('use_agent', True)}")

            if available_agents and browser_config.get("use_agent", True):
                # 使用本地 Agent 执行
                execution.execution_mode = "agent"
                self.db.flush()
                logger.info(f"✓ 发现 {len(available_agents)} 个可用 Agent，使用 Agent 执行任务")

                # 获取第一个可用的 Agent
                agent_id = list(available_agents.keys())[0]
                logger.info(f"使用 Agent: {agent_id}")

                # Agent 执行时默认显示浏览器（除非明确要求 headless）
                agent_browser_config = browser_config.copy()
                if "headless" not in agent_browser_config:
                    agent_browser_config["headless"] = False
                    logger.info("Agent 执行模式：显示浏览器")

                # 获取 manager 实例用于发送消息
                from app.api import agent as agent_module
                agent_mgr = agent_module.manager

                # 转换任务为 Agent 格式并下发
                logger.info(f"开始通过 Agent {agent_id} 执行任务...")
                result = await self._execute_via_agent(agent_id, task, agent_browser_config, agent_mgr)
                logger.info(f"Agent 执行完成，result: {result}")

                # 更新执行结果
                execution.completed_at = datetime.now(timezone.utc)
                started_at_aware = _ensure_datetime_aware(execution.started_at)
                execution.duration = (execution.completed_at - started_at_aware).total_seconds()

                # Agent 返回格式: {success, results: [{success, action, error}], message}
                # 需要从 results 数组计算步骤统计
                agent_results = result.get("results", [])
                total_steps = len(agent_results)
                passed_steps = sum(1 for r in agent_results if r.get("success"))
                failed_steps = total_steps - passed_steps

                logger.info(f"Agent 返回 {total_steps} 个步骤结果: {passed_steps} 成功, {failed_steps} 失败")

                if result.get("success"):
                    execution.status = "completed"
                    execution.result = "pass"
                    execution.total_steps = total_steps
                    execution.passed_steps = passed_steps
                    execution.failed_steps = failed_steps
                else:
                    execution.status = "completed"
                    execution.result = "fail"

                    # 获取第一个失败步骤的错误信息
                    error_info = None
                    for step_result in agent_results:
                        if not step_result.get("success"):
                            error_info = step_result.get("error", "Agent 执行失败")
                            break

                    execution.error_message = error_info or "Agent 执行失败"
                    execution.total_steps = total_steps
                    execution.passed_steps = passed_steps
                    execution.failed_steps = failed_steps

                self.db.commit()
                self.db.refresh(execution)

                return execution

            # 5. 没有 Agent 或不使用 Agent，在容器内执行
            execution.execution_mode = "direct"
            self.db.flush()
            logger.info("在容器内执行任务")

            # 6. 设置浏览器管理器
            await self._setup_browser(browser_config)

            # 7. 初始化关键字引擎和编排器
            self.keyword_engine = KeywordEngine(browser_manager=self.browser_manager)
            self._initialize_orchestrator()

            # 8. 委托给 TaskOrchestrator 执行
            execution = await self.task_orchestrator.orchestrate_task_execution(
                task=task,
                execution=execution,
                browser_config=browser_config
            )

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
            # 9. 清理浏览器
            if self.browser_manager:
                await self.browser_manager.close()

        return execution

    async def _setup_browser(self, browser_config: Dict[str, Any]):
        """
        设置浏览器管理器

        Args:
            browser_config: 浏览器配置
        """
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

    async def _execute_via_agent(
        self,
        agent_id: str,
        task: UITask,
        browser_config: dict,
        agent_mgr
    ) -> Dict[str, Any]:
        """
        通过 Agent 执行任务

        Args:
            agent_id: Agent ID
            task: 任务定义
            browser_config: 浏览器配置

        Returns:
            执行结果
        """
        logger.info(f"Executing via agent: {agent_id}")
        logger.info(f"task.scenario_ids = {task.scenario_ids} (type: {type(task.scenario_ids)})")

        # 加载场景和用例
        scenarios = []
        logger.info(f"开始加载场景，task.scenario_ids = {task.scenario_ids}")

        for idx, scenario_id in enumerate(task.scenario_ids or []):
            logger.info(f"处理 scenario_id #{idx}: {repr(scenario_id)} (type: {type(scenario_id)})")

            # 跳过无效的 scenario_id（空字典、空字符串等）
            if not scenario_id or not isinstance(scenario_id, (str, uuid.UUID)):
                logger.warning(f"跳过无效的 scenario_id: {scenario_id} (类型: {type(scenario_id)})")
                continue

            # 转换为 UUID 对象（SQLite + UUID 需要 Python UUID 对象）
            try:
                if isinstance(scenario_id, uuid.UUID):
                    scenario_id_uuid = scenario_id
                else:
                    scenario_id_uuid = uuid.UUID(str(scenario_id))
            except ValueError:
                logger.warning(f"跳过无效的 UUID 格式: {scenario_id}")
                continue

            logger.info(f"查询场景，UUID: {scenario_id_uuid}")
            scenario = self.db.query(UIScenario).filter(
                UIScenario.id == scenario_id_uuid
            ).first()

            if scenario:
                logger.info(f"✓ 找到场景: {scenario.name}")
                scenarios.append(scenario)
            else:
                logger.warning(f"✗ 场景不存在: {scenario_id_uuid}")

        # 构建任务结构
        task_structure = {
            "task_id": str(task.id),
            "task_name": task.name,
            "scenarios": []
        }

        total_steps = 0
        for scenario in scenarios:
            logger.info(f"处理场景: {scenario.name}")
            # 解析用例ID
            case_ids = scenario.case_ids or []
            logger.info(f"原始 case_ids: {case_ids}, 类型: {type(case_ids)}")

            if isinstance(case_ids, str):
                try:
                    case_ids = json.loads(case_ids)
                    logger.info(f"解析后的 case_ids: {case_ids}")
                except json.JSONDecodeError:
                    logger.error(f"JSON 解析失败: {case_ids}")
                    case_ids = []

            # 过滤无效的 case_id（空字典、空字符串等）
            valid_case_ids = []
            for idx, cid in enumerate(case_ids):
                logger.info(f"检查 case_id[{idx}]: {repr(cid)}, 类型: {type(cid)}")
                if cid and isinstance(cid, (str, uuid.UUID)) and str(cid).strip():
                    # 验证并转换为 UUID 对象
                    try:
                        if isinstance(cid, uuid.UUID):
                            valid_case_ids.append(cid)
                            logger.info(f"  ✓ 有效的 UUID 对象: {cid}")
                        else:
                            uuid_obj = uuid.UUID(str(cid))
                            valid_case_ids.append(uuid_obj)
                            logger.info(f"  ✓ 转换为 UUID: {cid} -> {uuid_obj}")
                    except ValueError as e:
                        logger.warning(f"  ✗ 跳过无效的 case_id UUID: {cid}, 错误: {e}")
                else:
                    logger.warning(f"  ✗ 跳过无效的 case_id: {cid} (类型: {type(cid)})")

            if not valid_case_ids:
                logger.warning(f"场景 {scenario.name} 没有有效的用例 ID")
                continue

            # 加载用例
            cases = self.db.query(UICase).filter(
                UICase.id.in_(valid_case_ids)
            ).all()

            scenario_data = {
                "scenario_id": str(scenario.id),
                "scenario_name": scenario.name,
                "execution_order": scenario.execution_order,
                "cases": []
            }

            for case in cases:
                # 解析步骤ID
                step_ids = case.step_ids or []
                if isinstance(step_ids, str):
                    try:
                        step_ids = json.loads(step_ids)
                    except json.JSONDecodeError:
                        step_ids = []

                # 过滤无效的 step_id
                valid_step_ids = []
                for sid in step_ids:
                    if sid and isinstance(sid, (str, uuid.UUID)) and str(sid).strip():
                        # 验证并转换为 UUID 对象
                        try:
                            if isinstance(sid, uuid.UUID):
                                valid_step_ids.append(sid)
                            else:
                                valid_step_ids.append(uuid.UUID(str(sid)))
                        except ValueError:
                            logger.warning(f"跳过无效的 step_id UUID: {sid}")
                    else:
                        logger.warning(f"跳过无效的 step_id: {sid} (类型: {type(sid)})")

                if not valid_step_ids:
                    logger.warning(f"用例 {case.name} 没有有效的步骤 ID")
                    # 仍然添加这个用例，只是没有步骤
                    total_steps += 0
                else:
                    total_steps += len(valid_step_ids)

                case_data = {
                    "case_id": str(case.id),
                    "case_name": case.name,
                    "description": case.description,
                    "steps": []
                }

                # 加载步骤
                if valid_step_ids:
                    steps = self.db.query(UIStep).filter(
                        UIStep.id.in_(valid_step_ids)
                    ).order_by(UIStep.step_order).all()
                else:
                    steps = []

                for step in steps:
                    keyword = self.db.query(Keyword).filter(
                        Keyword.id == step.keyword_id
                    ).first()

                    if keyword:
                        step_data = self._convert_step_to_agent_format(keyword, step.parameters or {})
                        if step_data:
                            step_data["step_order"] = step.step_order
                            step_data["step_name"] = step.step_name
                            step_data["continue_on_failure"] = step.continue_on_failure or False  # 添加 continue_on_failure
                            case_data["steps"].append(step_data)

                scenario_data["cases"].append(case_data)

            task_structure["scenarios"].append(scenario_data)

        logger.info(f"Prepared task with {total_steps} steps for agent execution")

        # 生成任务 ID
        task_execution_id = str(uuid.uuid4())
        logger.info(f"生成的任务执行 ID: {task_execution_id}")

        # 扁平化步骤为 Agent 期望的格式
        agent_steps = []
        for scenario in task_structure["scenarios"]:
            for case in scenario["cases"]:
                for step in case["steps"]:
                    agent_steps.append(step)

        # 构建 Agent 期望的任务消息格式
        task_message = {
            "type": "task",  # Agent 期望 "task" 而不是 "execute_task"
            "task_id": task_execution_id,
            "browser_type": browser_config.get("browser_type", "chromium"),
            "headless": browser_config.get("headless", False),
            "url": "",  # Agent 会从第一步 NAVIGATE 获取 URL
            "steps": agent_steps
        }
        logger.info(f"准备发送任务消息给 Agent {agent_id} (包含 {len(agent_steps)} 个步骤)")

        # 发送任务给 Agent
        sent = await agent_mgr.send_to_agent(agent_id, task_message)
        logger.info(f"发送任务结果: {sent}")
        if not sent:
            raise Exception(f"发送任务给 Agent {agent_id} 失败")

        logger.info(f"开始等待任务执行结果 (超时: 180秒)...")
        # 等待任务执行结果（使用任务 ID）
        wrapper = await agent_mgr.wait_for_task_result(
            task_execution_id,
            timeout=180.0  # 3分钟超时
        )
        logger.info(f"收到任务执行包装结果: {wrapper}")

        if wrapper is None:
            raise Exception(f"Agent {agent_id} 执行任务超时")

        # 从包装中提取实际的执行结果
        result = wrapper.get("result", {})
        logger.info(f"提取执行结果: {result}")
        logger.info(f"Agent 返回的 results 字段: {result.get('results', [])}")
        logger.info(f"Agent 返回的 results 长度: {len(result.get('results', []))}")

        # 为每个步骤创建 StepExecution 记录
        logger.info(f"准备创建步骤执行记录...")
        try:
            await self._create_step_executions_for_agent(
                execution=self.current_execution,
                task_structure=task_structure,
                agent_results=result.get("results", []),
                agent_id=agent_id
            )
            logger.info(f"✓ 步骤执行记录创建完成")
        except Exception as e:
            logger.error(f"✗ 创建步骤执行记录失败: {e}")
            logger.error(f"错误详情: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"堆栈跟踪:\n{traceback.format_exc()}")

        return result

    async def _create_step_executions_for_agent(
        self,
        execution: TestExecution,
        task_structure: dict,
        agent_results: list,
        agent_id: str
    ):
        """
        为 Agent 执行创建步骤执行记录

        Args:
            execution: 执行记录
            task_structure: 任务结构（包含 scenarios/cases/steps）
            agent_results: Agent 返回的步骤结果列表
            agent_id: Agent ID
        """
        logger.info(f"开始创建 {len(agent_results)} 个步骤执行记录")

        # 为 Agent 执行创建 scenario_execution 和 case_execution（使用第一个场景/用例）
        scenarios = task_structure.get("scenarios", [])
        if scenarios:
            scenario_info = scenarios[0]
            cases = scenario_info.get("cases", [])
            if cases:
                case_info = cases[0]

                # 创建 scenario_execution
                scenario_execution = ScenarioExecution(
                    id=uuid.uuid4(),
                    test_execution_id=execution.id,
                    scenario_id=scenario_info.get("scenario_id"),
                    status="completed" if all(r.get("success", False) for r in agent_results) else "failed",
                    result="pass" if all(r.get("success", False) for r in agent_results) else "fail",
                    total_steps=len(agent_results),
                    passed_steps=sum(1 for r in agent_results if r.get("success", False)),
                    failed_steps=sum(1 for r in agent_results if not r.get("success", False)),
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                    duration=execution.duration
                )
                self.db.add(scenario_execution)
                self.db.flush()  # 获取 ID

                # 创建 case_execution
                case_execution = CaseExecution(
                    id=uuid.uuid4(),
                    scenario_execution_id=scenario_execution.id,
                    test_execution_id=execution.id,
                    case_id=case_info.get("case_id"),
                    status="completed" if all(r.get("success", False) for r in agent_results) else "failed",
                    result="pass" if all(r.get("success", False) for r in agent_results) else "fail",
                    total_steps=len(agent_results),
                    passed_steps=sum(1 for r in agent_results if r.get("success", False)),
                    failed_steps=sum(1 for r in agent_results if not r.get("success", False)),
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                    duration=execution.duration
                )
                self.db.add(case_execution)
                self.db.flush()  # 获取 ID

                logger.info(f"✓ 创建 scenario_execution: {scenario_execution.id}")
                logger.info(f"✓ 创建 case_execution: {case_execution.id}")

        # 扁平化所有步骤（保留原始步骤信息）
        all_steps = []
        for scenario in task_structure.get("scenarios", []):
            for case in scenario.get("cases", []):
                for step in case.get("steps", []):
                    step["scenario_id"] = scenario.get("scenario_id")
                    step["scenario_name"] = scenario.get("scenario_name")
                    step["case_id"] = case.get("case_id")
                    step["case_name"] = case.get("case_name")
                    all_steps.append(step)

        # 遍历 Agent 返回的结果，创建 StepExecution 记录
        for idx, agent_result in enumerate(agent_results):
            if idx >= len(all_steps):
                logger.warning(f"Agent 返回的结果数 ({len(agent_results)}) 超过步骤数 ({len(all_steps)})")
                break

            step_info = all_steps[idx]
            step_result = agent_result  # {success, action, error, ...}

            # 创建 StepExecution 记录，关联到 case_execution
            step_execution = StepExecution(
                id=uuid.uuid4(),
                case_execution_id=case_execution.id,  # 关联到 case_execution
                step_id=None,  # Agent 步骤没有 UIStep ID
                keyword_id=None,
                # 步骤名称包含场景和用例上下文
                step_name=f"{step_info.get('scenario_name', 'Scenario')} > "
                          f"{step_info.get('case_name', 'Case')} > "
                          f"{step_info.get('step_name', f'Step {idx + 1}')}",
                step_order=idx,
                keyword_name=step_result.get("action", ""),
                category="agent",
                status="completed" if step_result.get("success") else "failed",
                result="pass" if step_result.get("success") else "fail",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration=0,  # Agent 没有返回每个步骤的耗时
                retry_attempt=0,
                continue_on_failure=step_info.get("continue_on_failure", False),  # 从步骤信息读取
                parameters=step_info.get("parameters", {}),  # 直接传 dict，不需要 json.dumps
                error_message=step_result.get("error") if not step_result.get("success") else None,
                # 存储 Agent 执行的详细信息
                output={
                    "action": step_result.get("action"),
                    "success": step_result.get("success"),
                    "scenario_id": str(step_info.get("scenario_id", "")),
                    "scenario_name": step_info.get("scenario_name", ""),
                    "case_id": str(step_info.get("case_id", "")),
                    "case_name": step_info.get("case_name", ""),
                }
            )

            self.db.add(step_execution)
            logger.info(f"  步骤 {idx + 1}: {step_result.get('action')} - "
                       f"{'✓ 通过' if step_result.get('success') else '✗ 失败'}")

        self.db.commit()
        logger.info(f"✓ 已创建 {len(agent_results)} 个步骤执行记录")

    def _convert_step_to_agent_format(self, keyword: Keyword, parameters: dict) -> Optional[dict]:
        """
        将步骤转换为 Agent 格式

        Args:
            keyword: 关键字定义
            parameters: 参数

        Returns:
            Agent 格式的步骤
        """
        try:
            # Agent 支持的操作映射
            action_mapping = {
                "NAVIGATE": "navigate",
                "CLICK": "click",
                "INPUT": "input",
                "WAIT_FOR_ELEMENT": "wait",
                "SCREENSHOT": "screenshot"
            }

            # 获取映射后的 action
            action = action_mapping.get(keyword.name, keyword.name.lower())

            # 处理参数转换
            agent_params = parameters.copy()

            # WAIT_FOR_ELEMENT 的参数转换
            if keyword.name == "WAIT_FOR_ELEMENT":
                agent_params = {
                    "selector": parameters.get("selector"),
                    "state": parameters.get("state", "visible"),
                    "timeout": parameters.get("timeout", 5000)
                }
                logger.info(f"转换 WAIT_FOR_ELEMENT -> wait, 参数: selector={agent_params['selector']}, state={agent_params['state']}, timeout={agent_params['timeout']}")

            agent_step = {
                "action": action,
                "parameters": agent_params
            }
            return agent_step
        except Exception as e:
            logger.error(f"Failed to convert step to agent format: {e}")
            return None
        """
        将步骤转换为 Agent 格式

        Args:
            keyword: 关键字定义
            parameters: 参数

        Returns:
            Agent 格式的步骤
        """
        try:
            # Agent 支持的操作映射
            # 后端关键字名称 -> Agent 操作名称
            action_mapping = {
                "NAVIGATE": "navigate",
                "CLICK": "click",
                "INPUT": "input",
                "WAIT_FOR_ELEMENT": "wait",  # 映射到 Agent 的 wait 操作
                "SCREENSHOT": "screenshot"
            }

            # 获取映射后的 action
            action = action_mapping.get(keyword.name, keyword.name.lower())

            # 处理参数转换
            agent_params = parameters.copy()

            # WAIT_FOR_ELEMENT 的参数转换
            # 后端: {selector, state, timeout}
            # Agent: {selector, state, timeout}
            if keyword.name == "WAIT_FOR_ELEMENT":
                # Agent 现在支持 state 参数
                agent_params = {
                    "selector": parameters.get("selector"),
                    "state": parameters.get("state", "visible"),  # visible/attached/hidden
                    "timeout": parameters.get("timeout", 5000)
                }
                logger.info(f"转换 WAIT_FOR_ELEMENT -> wait, 参数: selector={agent_params['selector']}, state={agent_params['state']}, timeout={agent_params['timeout']}")

            agent_step = {
                "action": action,
                "parameters": agent_params
            }
            return agent_step
        except Exception as e:
            logger.error(f"Failed to convert step to agent format: {e}")
            return None
