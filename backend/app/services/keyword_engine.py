"""
关键字引擎 - 主引擎

支持插件化的关键字注册和管理系统，提供可扩展的关键字执行能力。
"""
from typing import Dict, Any, Optional
import logging
from .keywords.base_engine import BaseKeywordEngine
from .keywords.api_keywords import APIKeywordEngine
from .keywords.ui_keywords import UIKeywordEngine
from .keywords.keyword_registry import keyword_registry

logger = logging.getLogger(__name__)


class KeywordEngine:
    """
    关键字引擎 - 主入口

    职责：
    - 支持插件化的关键字注册
    - 协调不同类型的关键字执行器
    - 提供统一的执行接口
    - 路由关键字到对应的执行器
    """

    def __init__(self, browser_manager=None, use_registry: bool = True):
        """
        初始化关键字引擎

        Args:
            browser_manager: PlaywrightBrowser 实例（用于 UI 关键字）
            use_registry: 是否使用注册表（默认 True，启用插件化）
        """
        self.browser_manager = browser_manager
        self.use_registry = use_registry

        # 初始化各个执行器（向后兼容）
        self.api_engine = APIKeywordEngine()
        self.ui_engine = UIKeywordEngine(browser_manager)

        # 如果使用注册表，注册内置关键字
        if use_registry:
            self._register_builtin_keywords()

    def _register_builtin_keywords(self) -> None:
        """注册内置关键字到注册表"""
        # 这里可以注册所有内置关键字
        # 为了向后兼容，暂时使用现有的执行器
        logger.info("📦 内置关键字已通过执行器加载")

    async def execute(
        self,
        keyword_def: Any,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行指定关键字

        Args:
            keyword_def: 关键字定义（SQLAlchemy 模型或字典）
            parameters: 关键字参数
            context: 执行上下文

        Returns:
            执行结果字典，包含 success、data 等字段
        """
        # 兼容 SQLAlchemy 对象和字典
        if hasattr(keyword_def, "name"):
            # SQLAlchemy 模型
            keyword_name = keyword_def.name
            category = keyword_def.category
        else:
            # 字典
            keyword_name = keyword_def.get("name")
            category = keyword_def.get("category")

        logger.info(f"执行关键字: {keyword_name} (类别: {category})")

        # 首先尝试从注册表执行（插件化关键字）
        if self.use_registry and keyword_registry.exists(category, keyword_name):
            return await keyword_registry.execute(
                category=category,
                name=keyword_name,
                parameters=parameters,
                context=context
            )

        # 回退到传统执行器（向后兼容）
        if category == "api":
            return await self.api_engine.execute(keyword_def, parameters, context)
        elif category == "ui":
            return await self.ui_engine.execute(keyword_def, parameters, context)
        else:
            return {
                "success": False,
                "error": f"未知类别: {category}"
            }

    def register_keyword(
        self,
        category: str,
        name: str,
        handler: callable,
        description: str = "",
        parameters_schema: Optional[Dict] = None,
        author: str = "",
        version: str = "1.0.0"
    ) -> None:
        """
        注册自定义关键字（便捷方法）

        Args:
            category: 关键字类别（api, ui, custom）
            name: 关键字名称
            handler: 处理函数
            description: 描述
            parameters_schema: 参数 Schema
            author: 作者
            version: 版本

        Example:
            engine = KeywordEngine()
            engine.register_keyword(
                category="custom",
                name="MY_ACTION",
                handler=lambda params, ctx: {"success": True},
                description="我的自定义操作"
            )
        """
        if not self.use_registry:
            logger.warning("注册表未启用，无法注册自定义关键字")
            return

        keyword_registry.register_handler(
            category=category,
            name=name,
            handler=handler,
            description=description,
            parameters_schema=parameters_schema,
            author=author,
            version=version
        )

    def list_keywords(self, category: Optional[str] = None) -> list:
        """
        列出所有可用关键字

        Args:
            category: 过滤类别（如果为 None，返回所有）

        Returns:
            关键字列表
        """
        if self.use_registry:
            handlers = keyword_registry.list_keywords(category)
            return [
                {
                    "name": h.name,
                    "category": h.category,
                    "description": h.description,
                    "author": h.author,
                    "version": h.version
                }
                for h in handlers
            ]
        else:
            # 回退到传统方式
            return []

    def get_keyword_info(self, category: str, name: str) -> Optional[Dict]:
        """
        获取关键字信息

        Args:
            category: 类别
            name: 名称

        Returns:
            关键字信息字典
        """
        if self.use_registry:
            return keyword_registry.get_keyword_info(category, name)
        return None

    # 向后兼容的方法（如果外部直接调用）

    async def _execute_api_keyword(
        self,
        keyword_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行 API 测试关键字（向后兼容）"""
        # 构造临时关键字定义
        keyword_def = {"name": keyword_name, "category": "api"}
        return await self.api_engine.execute(keyword_def, parameters, context)

    async def _execute_ui_keyword(
        self,
        keyword_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行 UI 测试关键字（向后兼容）"""
        # 构造临时关键字定义
        keyword_def = {"name": keyword_name, "category": "ui"}
        return await self.ui_engine.execute(keyword_def, parameters, context)
