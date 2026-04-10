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
from ...models.execution import TestExecution
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
        browser_config: dict
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

        # 加载场景和用例
        scenarios = []
        for scenario_id in task.scenario_ids or []:
            # 跳过无效的 scenario_id（空字典、空字符串等）
            if not scenario_id or not isinstance(scenario_id, (str, uuid.UUID)):
                logger.warning(f"跳过无效的 scenario_id: {scenario_id} (类型: {type(scenario_id)})")
                continue

            # 确保 scenario_id 是字符串
            scenario_id_str = str(scenario_id) if isinstance(scenario_id, uuid.UUID) else scenario_id

            # 验证 UUID 格式
            try:
                uuid.UUID(scenario_id_str)
            except ValueError:
                logger.warning(f"跳过无效的 UUID 格式: {scenario_id_str}")
                continue

            scenario = self.db.query(UIScenario).filter(
                UIScenario.id == scenario_id_str
            ).first()
            if scenario:
                scenarios.append(scenario)

        # 构建任务结构
        task_structure = {
            "task_id": str(task.id),
            "task_name": task.name,
            "scenarios": []
        }

        total_steps = 0
        for scenario in scenarios:
            # 解析用例ID
            case_ids = scenario.case_ids
            if isinstance(case_ids, str):
                try:
                    case_ids = json.loads(case_ids)
                except json.JSONDecodeError:
                    case_ids = []

            # 加载用例
            from ..models.ui_task import UICase
            cases = self.db.query(UICase).filter(
                UICase.id.in_(case_ids)
            ).all()

            scenario_data = {
                "scenario_id": str(scenario.id),
                "scenario_name": scenario.name,
                "execution_order": scenario.execution_order,
                "cases": []
            }

            for case in cases:
                # 解析步骤ID
                step_ids = case.step_ids
                if isinstance(step_ids, str):
                    try:
                        step_ids = json.loads(step_ids)
                    except json.JSONDecodeError:
                        step_ids = []

                total_steps += len(step_ids)

                case_data = {
                    "case_id": str(case.id),
                    "case_name": case.name,
                    "description": case.description,
                    "steps": []
                }

                # 加载步骤
                from ..models.ui_task import UIStep
                from ..models.keyword import Keyword

                steps = self.db.query(UIStep).filter(
                    UIStep.id.in_(step_ids)
                ).order_by(UIStep.step_order).all()

                for step in steps:
                    keyword = self.db.query(Keyword).filter(
                        Keyword.id == step.keyword_id
                    ).first()

                    if keyword:
                        step_data = self._convert_step_to_agent_format(keyword, step.parameters or {})
                        if step_data:
                            step_data["step_order"] = step.step_order
                            step_data["step_name"] = step.step_name
                            case_data["steps"].append(step_data)

                scenario_data["cases"].append(case_data)

            task_structure["scenarios"].append(scenario_data)

        logger.info(f"Prepared task with {total_steps} steps for agent execution")

        # 发送任务给 Agent
        result = await agent_manager.manager.send_task_to_agent(
            agent_id=agent_id,
            task_data=task_structure,
            browser_config=browser_config
        )

        return result

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
            # Agent 格式
            agent_step = {
                "keyword": keyword.name,
                "category": keyword.category,
                "parameters": parameters
            }
            return agent_step
        except Exception as e:
            logger.error(f"Failed to convert step to agent format: {e}")
            return None
