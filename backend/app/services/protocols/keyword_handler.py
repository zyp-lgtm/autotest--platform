"""
关键字处理器协议

定义关键字处理器的接口，支持插件化关键字实现
"""
from typing import Protocol, Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class HandlerResult:
    """
    处理器执行结果

    Attributes:
        success: 是否成功
        message: 结果消息
        data: 返回数据（可选）
        error: 错误信息（失败时）
        screenshot_path: 截图路径（可选）
        duration: 执行时长（毫秒）
    """
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    duration: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "screenshot_path": self.screenshot_path,
            "duration": self.duration
        }


class KeywordHandler(Protocol):
    """
    关键字处理器协议

    所有关键字处理器必须实现此协议
    """

    @property
    def name(self) -> str:
        """
        关键字名称

        Returns:
            关键字名称（如 "CLICK", "INPUT"）
        """
        ...

    @property
    def category(self) -> str:
        """
        关键字类别

        Returns:
            类别（如 "navigation", "interaction", "wait", "assertion"）
        """
        ...

    @property
    def description(self) -> str:
        """
        关键字描述

        Returns:
            关键字功能描述
        """
        ...

    @property
    def parameter_schema(self) -> Dict[str, Any]:
        """
        参数模式（JSON Schema 格式）

        Returns:
            参数定义字典
        """
        ...

    @property
    def examples(self) -> List[Dict[str, Any]]:
        """
        使用示例

        Returns:
            示例列表
        """
        ...

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        验证参数

        Args:
            parameters: 参数字典

        Raises:
            ValueError: 参数验证失败
        """
        ...

    async def execute(
        self,
        context: 'ExecutionContext',  # noqa: F821
        parameters: Dict[str, Any]
    ) -> HandlerResult:
        """
        执行关键字

        Args:
            context: 执行上下文（包含 page, agent 等资源）
            parameters: 关键字参数

        Returns:
            HandlerResult: 执行结果
        """
        ...

    def get_timeout(self, parameters: Dict[str, Any]) -> int:
        """
        获取超时时间

        Args:
            parameters: 参数字典

        Returns:
            超时时间（毫秒），默认 30000
        """
        return parameters.get('timeout', 30000)

    async def before_execute(self, context: 'ExecutionContext', parameters: Dict[str, Any]) -> None:  # noqa: F821
        """
        执行前钩子

        Args:
            context: 执行上下文
            parameters: 参数字典
        """
        pass

    async def after_execute(
        self,
        context: 'ExecutionContext',  # noqa: F821
        parameters: Dict[str, Any],
        result: HandlerResult
    ) -> HandlerResult:
        """
        执行后钩子

        Args:
            context: 执行上下文
            parameters: 参数字典
            result: 执行结果

        Returns:
            可能被修改的执行结果
        """
        return result

    async def on_error(
        self,
        context: 'ExecutionContext',  # noqa: F821
        parameters: Dict[str, Any],
        error: Exception
    ) -> HandlerResult:
        """
        错误处理钩子

        Args:
            context: 执行上下文
            parameters: 参数字典
            error: 捕获的异常

        Returns:
            包含错误信息的执行结果
        """
        return HandlerResult(
            success=False,
            message=f"执行失败: {str(error)}",
            error=str(error)
        )


class HandlerRegistry(Protocol):
    """
    处理器注册表协议

    管理关键字处理器的注册和查找
    """

    def register(self, handler: KeywordHandler) -> None:
        """
        注册处理器

        Args:
            handler: 关键字处理器
        """
        ...

    def unregister(self, name: str) -> None:
        """
        注销处理器

        Args:
            name: 处理器名称
        """
        ...

    def get(self, name: str) -> Optional[KeywordHandler]:
        """
        获取处理器

        Args:
            name: 处理器名称

        Returns:
            处理器实例，不存在返回 None
        """
        ...

    def get_or_raise(self, name: str) -> KeywordHandler:
        """
        获取处理器，不存在则抛出异常

        Args:
            name: 处理器名称

        Returns:
            处理器实例

        Raises:
            KeyError: 处理器不存在
        """
        ...

    def list_all(self) -> List[KeywordHandler]:
        """
        获取所有处理器

        Returns:
            处理器列表
        """
        ...

    def list_by_category(self, category: str) -> List[KeywordHandler]:
        """
        根据类别获取处理器

        Args:
            category: 类别名称

        Returns:
            该类别的处理器列表
        """
        ...

    def get_categories(self) -> List[str]:
        """
        获取所有类别

        Returns:
            类别列表
        """
        ...
