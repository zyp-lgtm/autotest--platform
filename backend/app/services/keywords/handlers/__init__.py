"""
关键字处理器包

提供插件化的关键字处理器实现
"""
from .base_handler import BaseKeywordHandler
from .navigation import NAVIGATION_HANDLERS
from .interaction import INTERACTION_HANDLERS
from .wait import WAIT_HANDLERS
from .assertion import ASSERTION_HANDLERS

__all__ = [
    "BaseKeywordHandler",
    "NAVIGATION_HANDLERS",
    "INTERACTION_HANDLERS",
    "WAIT_HANDLERS",
    "ASSERTION_HANDLERS",
]

# 所有内置 Handler 的集合
ALL_HANDLERS = [
    *NAVIGATION_HANDLERS,
    *INTERACTION_HANDLERS,
    *WAIT_HANDLERS,
    *ASSERTION_HANDLERS,
]
