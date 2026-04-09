"""
步骤执行器

负责执行单个测试步骤，包括重试逻辑、错误处理等
"""
import logging
from typing import Dict, Any, Optional
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from sqlalchemy.orm import Session

from ...models.ui_task import UITask, UIScenario, UICase, UIStep
from ...models.execution import StepExecution
from ...models.keyword import Keyword
from ...services.keyword_engine import KeywordEngine
from ...services.playwright_browser import PlaywrightBrowser
from ...services.debug_collector import DebugInfoCollector
from ...services.error_classifier import ErrorClassifier
from ...core.interfaces import IKeywordEngine, IBrowserManager, IDebugCollector

logger = logging.getLogger(__name__)


class StepExecutor:
    """步骤执行器"""

    def __init__(
        self,
        db: Session,
        keyword_engine: IKeywordEngine,  # 使用接口而非具体实现
        browser_manager: IBrowserManager,  # 使用接口而非具体实现
        debug_collector: IDebugCollector  # 使用接口而非具体实现
    ):
        """
        初始化步骤执行器

        Args:
            db: 数据库会话
            keyword_engine: 关键字引擎（接口）
            browser_manager: 浏览器管理器（接口）
            debug_collector: 调试收集器（接口）
        """
        self.db = db
        self.keyword_engine = keyword_engine
        self.browser_manager = browser_manager
        self.debug_collector = debug_collector
        self.error_classifier = ErrorClassifier()

    async def execute_step(
        self,
        step: UIStep,
        case_execution,
        scenario_execution,
        task_execution
    ) -> StepExecution:
        """
        执行单个步骤

        Args:
            step: 步骤定义
            case_execution: 用例执行记录
            scenario_execution: 场景执行记录
            task_execution: 任务执行记录

        Returns:
            StepExecution: 步骤执行记录
        """
        # 创建步骤执行记录
        step_execution = self._create_step_execution_record(step, case_execution, scenario_execution, task_execution)

        try:
            # 获取关键字定义
            keyword = self.db.query(Keyword).filter(Keyword.id == step.keyword_id).first()
            if not keyword:
                raise ValueError(f"关键字不存在: {step.keyword_id}")

            # 解析参数
            parameters = step.parameters or {}

            # 记录开始时间
            from datetime import datetime, timezone
            step_execution.started_at = datetime.now(timezone.utc)

            # 执行关键字
            result = await self.keyword_engine.execute(
                keyword,
                parameters,
                {
                    "page": await self.browser_manager.get_page(),
                    "browser_manager": self.browser_manager
                }
            )

            # 记录结束时间
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration = (
                step_execution.completed_at - step_execution.started_at
            ).total_seconds()

            # 处理结果
            if result.get("success"):
                step_execution.status = "passed"
                step_execution.result = "pass"
                step_execution.output = result.get("data")
            else:
                error_msg = result.get("error", "未知错误")

                # 检查是否需要重试
                if self._should_retry_step(step, error_msg):
                    step_execution.status = "pending"
                    step_execution.retry_attempt = (step_execution.retry_attempt or 0) + 1
                    step_execution.retry_of = step_execution.id  # 指向原始步骤
                    logger.warning(f"步骤执行失败，准备重试 ({step_execution.retry_attempt}次): {error_msg}")
                else:
                    step_execution.status = "failed"
                    step_execution.result = "fail"
                    step_execution.error_message = error_msg

                    # 分类错误
                    error_info = self.error_classifier.classify(
                        error_msg,
                        keyword=keyword.name,
                        parameters=parameters
                    )
                    step_execution.error_info = error_info

            # 保存执行记录
            self.db.add(step_execution)
            self.db.commit()
            self.db.refresh(step_execution)

        except Exception as e:
            logger.error(f"步骤 {step.id} 执行失败: {e}")

            # 更新执行状态
            step_execution.status = "failed"
            step_execution.result = "fail"
            step_execution.error_message = str(e)
            step_execution.completed_at = datetime.now(timezone.utc)

            # 计算持续时间
            if step_execution.started_at:
                started_at = step_execution.started_at.replace(tzinfo=timezone.utc)
                step_execution.duration = (
                    step_execution.completed_at - started_at
                ).total_seconds()

            self.db.add(step_execution)
            self.db.commit()
            self.db.refresh(step_execution)

        return step_execution

    def _should_retry_step(self, step: UIStep, error_message: str) -> bool:
        """
        判断是否应该重试步骤

        Args:
            step: 步骤定义
            error_message: 错误信息

        Returns:
            是否应该重试
        """
        max_retries = 3  # 最大重试次数
        current_retry = step.execution.retry_attempt or 0 if hasattr(step, 'execution') else 0

        # 超过最大重试次数
        if current_retry >= max_retries:
            return False

        # 检查是否启用了继续执行
        if not step.continue_on_failure:
            return False

        # 检查错误类型是否可重试
        retryable_errors = [
            "TimeoutError",
            "NetworkError",
            "ConnectionError",
            "超时",
            "网络",
            "连接"
        ]

        return any(err in error_message for err in retryable_errors)

    def _create_step_execution_record(
        self,
        step: UIStep,
        case_execution,
        scenario_execution,
        task_execution
    ) -> StepExecution:
        """
        创建步骤执行记录

        Args:
            step: 步骤定义
            case_execution: 用例执行记录
            scenario_execution: 场景执行记录
            task_execution: 任务执行记录

        Returns:
            StepExecution: 步骤执行记录
        """
        import uuid
        from datetime import datetime, timezone

        step_execution = StepExecution(
            id=uuid.uuid4(),
            case_execution_id=case_execution.id,
            step_id=step.id,
            keyword_id=step.keyword_id,
            scenario_execution_id=scenario_execution.id,
            test_execution_id=task_execution.id,
            step_name=step.step_name,
            step_order=step.step_order,
            keyword_name="",  # 稍后从关键字获取
            category=step.step_type,
            status="pending",
            result="",
            started_at=datetime.now(timezone.utc),
            retry_attempt=0,
            continue_on_failure=step.continue_on_failure,
            parameters=step.parameters or {},
            screenshot_config=step.screenshot_config or {}
        )

        return step_execution
