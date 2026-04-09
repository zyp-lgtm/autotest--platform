"""
关键字引擎 - 主引擎

协调 API 和 UI 关键字执行器，提供统一的接口
"""
from typing import Dict, Any
import logging
from .keywords.base_engine import BaseKeywordEngine
from .keywords.api_keywords import APIKeywordEngine
from .keywords.ui_keywords import UIKeywordEngine

logger = logging.getLogger(__name__)


class KeywordEngine:
    """
    关键字引擎 - 主入口

    职责：
    - 协调不同类型的关键字执行器
    - 提供统一的执行接口
    - 路由关键字到对应的执行器
    """

    def __init__(self, browser_manager=None):
        """
        初始化关键字引擎

        Args:
            browser_manager: PlaywrightBrowser 实例（用于 UI 关键字）
        """
        self.browser_manager = browser_manager

        # 初始化各个执行器
        self.api_engine = APIKeywordEngine()
        self.ui_engine = UIKeywordEngine(browser_manager)

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

        # 根据类别路由到对应的执行器
        if category == "api":
            return await self.api_engine.execute(keyword_def, parameters, context)
        elif category == "ui":
            return await self.ui_engine.execute(keyword_def, parameters, context)
        else:
            return {
                "success": False,
                "error": f"未知类别: {category}"
            }

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
