"""
Repository 层

提供统一的数据访问接口，封装数据库操作细节。
"""
from .base import BaseRepository
from .task_repository import TaskRepository
from .execution_repository import ExecutionRepository
from .keyword_repository import KeywordRepository
from .user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "TaskRepository",
    "ExecutionRepository",
    "KeywordRepository",
    "UserRepository",
]
