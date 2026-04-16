"""
协议接口层

定义系统中关键组件的抽象接口，支持依赖注入和多态实现
"""
from .keyword_handler import KeywordHandler, HandlerResult
from .executor import TaskExecutorProtocol, ExecutionResult
from .agent import AgentClientProtocol

__all__ = [
    "KeywordHandler",
    "HandlerResult",
    "TaskExecutorProtocol",
    "ExecutionResult",
    "AgentClientProtocol",
]
