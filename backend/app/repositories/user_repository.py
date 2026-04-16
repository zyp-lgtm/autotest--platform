"""
用户仓储

处理用户数据访问
"""
from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
import logging

from app.repositories.base import BaseRepository
from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """用户仓储"""

    def __init__(self, session: Session):
        super().__init__(session, User)

    def get_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户

        Args:
            username: 用户名

        Returns:
            用户对象
        """
        return self.session.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户

        Args:
            email: 邮箱地址

        Returns:
            用户对象
        """
        return self.session.query(User).filter(User.email == email).first()

    def username_exists(self, username: str) -> bool:
        """
        检查用户名是否存在

        Args:
            username: 用户名

        Returns:
            用户名是否已存在
        """
        return self.session.query(User).filter(
            User.username == username
        ).first() is not None

    def email_exists(self, email: str) -> bool:
        """
        检查邮箱是否存在

        Args:
            email: 邮箱地址

        Returns:
            邮箱是否已存在
        """
        return self.session.query(User).filter(
            User.email == email
        ).first() is not None

    def get_active_users(self) -> List[User]:
        """
        获取所有活跃用户

        Returns:
            活跃用户列表
        """
        return self.session.query(User).filter(
            User.is_active == True
        ).all()

    def search_users(self, query: str, limit: int = 20) -> List[User]:
        """
        搜索用户

        Args:
            query: 搜索关键词
            limit: 限制返回数量

        Returns:
            匹配的用户列表
        """
        return self.session.query(User).filter(
            (User.username.ilike(f"%{query}%")) |
            (User.email.ilike(f"%{query}%")) |
            (User.full_name.ilike(f"%{query}%"))
        ).limit(limit).all()
