"""
关键字 Handler 加载器

自动发现并注册所有 Handler 类到关键字注册表
"""
import logging
from typing import List
from ..keywords.keyword_registry import keyword_registry
from ..protocols.keyword_handler import KeywordHandler

logger = logging.getLogger(__name__)


class HandlerLoader:
    """
    Handler 加载器

    自动扫描并注册所有 Handler 实例
    """

    def __init__(self):
        """初始化加载器"""
        self._handlers: List[KeywordHandler] = []

    def register_handlers(self, handlers: List[KeywordHandler]) -> None:
        """
        批量注册 Handler 到注册表

        Args:
            handlers: Handler 实例列表
        """
        for handler in handlers:
            self._register_single_handler(handler)

        logger.info(f"✅ 已注册 {len(handlers)} 个关键字 Handler")

    def _register_single_handler(self, handler: KeywordHandler) -> None:
        """
        注册单个 Handler

        Args:
            handler: Handler 实例
        """
        # 创建适配器函数，将 Handler.execute 方法适配为注册表期望的格式
        async def handler_adapter(parameters: dict, context: dict) -> dict:
            """Handler 适配器"""
            result = await handler.execute(context, parameters)
            return result.to_dict()

        # 注册到注册表
        keyword_registry.register_handler(
            category=handler.category,
            name=handler.name,
            handler=handler_adapter,
            description=handler.description,
            parameters_schema=handler.parameter_schema,
            author="System",
            version="1.0.0"
        )

        logger.debug(f"✅ 注册 Handler: {handler.category}.{handler.name}")

    def register_builtin_handlers(self) -> None:
        """
        注册所有内置 Handler

        从各个 handler 模块导入并注册
        """
        # 导入所有 Handler 模块
        from .handlers.navigation import NAVIGATION_HANDLERS
        from .handlers.interaction import INTERACTION_HANDLERS
        from .handlers.wait import WAIT_HANDLERS
        from .handlers.assertion import ASSERTION_HANDLERS

        # 收集所有 Handler
        all_handlers = []
        all_handlers.extend(NAVIGATION_HANDLERS)
        all_handlers.extend(INTERACTION_HANDLERS)
        all_handlers.extend(WAIT_HANDLERS)
        all_handlers.extend(ASSERTION_HANDLERS)

        # 注册所有 Handler
        self.register_handlers(all_handlers)

        logger.info(f"📦 内置关键字加载完成: {len(all_handlers)} 个")


# 全局加载器实例
handler_loader = HandlerLoader()


def register_all_handlers() -> None:
    """
    注册所有内置 Handler 的便捷函数

    Example:
        from app.services.keywords.handler_loader import register_all_handlers
        register_all_handlers()
    """
    handler_loader.register_builtin_handlers()


# 自动注册（当模块被导入时）
# register_all_handlers()  # 取消注释以启用自动注册
