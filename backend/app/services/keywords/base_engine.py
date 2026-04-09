"""
关键字引擎基础类

定义关键字引擎的接口和基础功能
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseKeywordEngine(ABC):
    """关键字引擎基础类"""

    @abstractmethod
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
        pass

    def _extract_keyword_info(self, keyword_def: Any) -> tuple[str, str]:
        """
        从关键字定义中提取名称和类别

        Args:
            keyword_def: 关键字定义（SQLAlchemy 模型或字典）

        Returns:
            (keyword_name, category) 元组
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

        return keyword_name, category

    def _success_response(self, data: Any = None) -> Dict[str, Any]:
        """创建成功响应"""
        return {
            "success": True,
            "data": data
        }

    def _error_response(self, error: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "success": False,
            "error": error
        }
