from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.variable_resolver import VariableResolver
from app.services.keyword_engine import KeywordEngine
import logging

logger = logging.getLogger(__name__)


class TestExecutor:
    """执行测试用例并记录结果"""

    def __init__(self, db: Session):
        self.db = db
        self.variable_resolver = VariableResolver()
        self.keyword_engine = KeywordEngine()

    async def execute_step(
        self,
        step: Any,
        context: Dict[str, Any],
        execution_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个步骤"""

        logger.info(f"执行步骤: {step.step_name}")

        # 解析参数中的变量
        resolved_params = {}
        for key, value in step.parameters.items():
            if isinstance(value, str):
                resolved_params[key] = self.variable_resolver.resolve(value, context)
            elif isinstance(value, dict):
                resolved_params[key] = {
                    k: self.variable_resolver.resolve(v, context) if isinstance(v, str) else v
                    for k, v in value.items()
                }
            else:
                resolved_params[key] = value

        # 执行关键字
        result = await self.keyword_engine.execute(
            keyword_def={
                "name": step.keyword.name,
                "category": step.keyword.category
            },
            parameters=resolved_params,
            context=context
        )

        return result