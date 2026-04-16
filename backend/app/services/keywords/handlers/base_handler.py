"""
基础 Handler 类

所有关键字处理器的基类
"""
from typing import Dict, Any
import logging
from app.services.protocols.keyword_handler import KeywordHandler, HandlerResult

logger = logging.getLogger(__name__)


class BaseKeywordHandler(KeywordHandler):
    """
    关键字处理器基类

    提供通用的实现，子类只需实现 execute 方法
    """

    def __init__(
        self,
        name: str,
        category: str,
        description: str = "",
        parameter_schema: Dict[str, Any] = None,
        examples: list = None
    ):
        """
        初始化处理器

        Args:
            name: 关键字名称
            category: 关键字类别
            description: 描述
            parameter_schema: 参数 JSON Schema
            examples: 使用示例
        """
        self._name = name
        self._category = category
        self._description = description
        self._parameter_schema = parameter_schema or {}
        self._examples = examples or []

    @property
    def name(self) -> str:
        return self._name

    @property
    def category(self) -> str:
        return self._category

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameter_schema(self) -> Dict[str, Any]:
        return self._parameter_schema

    @property
    def examples(self) -> list:
        return self._examples

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        验证参数

        检查必需参数是否存在，类型是否正确
        """
        required_params = self._parameter_schema.get("required", [])
        properties = self._parameter_schema.get("properties", {})

        # 检查必需参数
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"缺少必需参数: {param}")

            # 检查类型
            param_schema = properties.get(param, {})
            expected_type = param_schema.get("type")
            if expected_type:
                value = parameters[param]
                if expected_type == "string" and not isinstance(value, str):
                    raise ValueError(f"参数 {param} 应为字符串类型")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    raise ValueError(f"参数 {param} 应为数字类型")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    raise ValueError(f"参数 {param} 应为布尔类型")
                elif expected_type == "array" and not isinstance(value, list):
                    raise ValueError(f"参数 {param} 应为数组类型")
                elif expected_type == "object" and not isinstance(value, dict):
                    raise ValueError(f"参数 {param} 应为对象类型")

    async def before_execute(self, context, parameters: Dict[str, Any]) -> None:
        """执行前钩子（子类可覆盖）"""
        pass

    async def after_execute(
        self,
        context,
        parameters: Dict[str, Any],
        result: HandlerResult
    ) -> HandlerResult:
        """执行后钩子（子类可覆盖）"""
        return result

    async def on_error(
        self,
        context,
        parameters: Dict[str, Any],
        error: Exception
    ) -> HandlerResult:
        """错误处理钩子（子类可覆盖）"""
        return HandlerResult(
            success=False,
            message=f"执行失败: {str(error)}",
            error=str(error)
        )

    async def execute(
        self,
        context: 'ExecutionContext',
        parameters: Dict[str, Any]
    ) -> HandlerResult:
        """
        执行关键字（模板方法）

        子类应实现 _execute_logic 方法
        """
        # 验证参数
        self.validate_parameters(parameters)

        # 执行前钩子
        await self.before_execute(context, parameters)

        try:
            # 执行核心逻辑（由子类实现）
            import time
            start_time = time.time()

            result_data = await self._execute_logic(context, parameters)

            duration = int((time.time() - start_time) * 1000)

            # 构造成功结果
            result = HandlerResult(
                success=True,
                message=self.description or "执行成功",
                data=result_data,
                duration=duration
            )

            # 执行后钩子
            result = await self.after_execute(context, parameters, result)
            return result

        except Exception as e:
            logger.error(f"关键字 {self.name} 执行失败: {e}", exc_info=True)
            return await self.on_error(context, parameters, e)

    async def _execute_logic(
        self,
        context: 'ExecutionContext',
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行核心逻辑（子类必须实现）

        Args:
            context: 执行上下文
            parameters: 参数

        Returns:
            返回数据
        """
        raise NotImplementedError("子类必须实现 _execute_logic 方法")
