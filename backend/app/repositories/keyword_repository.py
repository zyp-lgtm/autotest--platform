"""
关键字仓储

处理关键字的数据访问
"""
from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
import logging

from app.repositories.base import BaseRepository
from app.models.keyword import Keyword

logger = logging.getLogger(__name__)


class KeywordRepository(BaseRepository):
    """关键字仓储"""

    def __init__(self, session: Session):
        super().__init__(session, Keyword)

    def get_by_category(self, category: str) -> List[Keyword]:
        """
        根据类别获取关键字

        Args:
            category: 关键字类别

        Returns:
            关键字列表
        """
        return self.session.query(Keyword).filter(
            Keyword.category == category
        ).order_by(Keyword.name).all()

    def get_categories(self) -> List[str]:
        """
        获取所有关键字类别

        Returns:
            类别列表
        """
        categories = self.session.query(Keyword.category).distinct().all()
        return [cat[0] for cat in categories]

    def get_valid_keywords(self) -> List[Keyword]:
        """
        获取所有有效的关键字

        Returns:
            有效关键字列表
        """
        return self.session.query(Keyword).filter(
            Keyword.is_valid == True
        ).order_by(Keyword.category, Keyword.name).all()

    def get_by_name(self, name: str) -> Optional[Keyword]:
        """
        根据名称获取关键字

        Args:
            name: 关键字名称

        Returns:
            关键字对象
        """
        return self.session.query(Keyword).filter(Keyword.name == name).first()

    def search(self, query: str, limit: int = 20) -> List[Keyword]:
        """
        搜索关键字

        Args:
            query: 搜索关键词
            limit: 限制返回数量

        Returns:
            匹配的关键字列表
        """
        return self.session.query(Keyword).filter(
            Keyword.name.ilike(f"%{query}%")
        ).limit(limit).all()

    def get_by_categories(self, categories: List[str]) -> List[Keyword]:
        """
        根据多个类别获取关键字

        Args:
            categories: 类别列表

        Returns:
            关键字列表
        """
        return self.session.query(Keyword).filter(
            Keyword.category.in_(categories)
        ).order_by(Keyword.category, Keyword.name).all()
