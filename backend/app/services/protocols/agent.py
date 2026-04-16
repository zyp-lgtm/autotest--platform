"""
Agent 客户端协议

定义 Agent 通信的接口
"""
from typing import Protocol, Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class AgentInfo:
    """
    Agent 信息

    Attributes:
        id: Agent ID
        status: Agent 状态 (connected, busy, disconnected)
        capabilities: 能力列表
        metadata: 元数据
        connected_at: 连接时间
    """
    id: str
    status: str
    capabilities: List[str]
    metadata: Dict[str, Any]
    connected_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "status": self.status,
            "capabilities": self.capabilities,
            "metadata": self.metadata,
            "connected_at": self.connected_at
        }


@dataclass
class AgentActionResult:
    """
    Agent 操作结果

    Attributes:
        success: 是否成功
        action: 操作类型
        results: 结果列表
        message: 消息
        error: 错误信息
    """
    success: bool
    action: str
    results: List[Dict[str, Any]]
    message: str
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "action": self.action,
            "results": self.results,
            "message": self.message,
            "error": self.error
        }


class AgentClientProtocol(Protocol):
    """
    Agent 客户端协议

    定义与 Agent 通信的标准接口
    """

    async def connect(self, agent_id: str) -> bool:
        """
        连接 Agent

        Args:
            agent_id: Agent ID

        Returns:
            是否成功连接
        """
        ...

    async def disconnect(self, agent_id: str) -> bool:
        """
        断开 Agent 连接

        Args:
            agent_id: Agent ID

        Returns:
            是否成功断开
        """
        ...

    async def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """
        获取 Agent 信息

        Args:
            agent_id: Agent ID

        Returns:
            Agent 信息
        """
        ...

    async def list_agents(self) -> List[AgentInfo]:
        """
        获取所有 Agent

        Returns:
            Agent 信息列表
        """
        ...

    async def execute_actions(
        self,
        agent_id: str,
        actions: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> AgentActionResult:
        """
        执行操作序列

        Args:
            agent_id: Agent ID
            actions: 操作列表
            context: 执行上下文

        Returns:
            AgentActionResult: 执行结果
        """
        ...

    async def send_command(
        self,
        agent_id: str,
        command: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送命令

        Args:
            agent_id: Agent ID
            command: 命令名称
            params: 命令参数

        Returns:
            命令执行结果
        """
        ...

    async def ping(self, agent_id: str) -> bool:
        """
        检查 Agent 存活状态

        Args:
            agent_id: Agent ID

        Returns:
            Agent 是否存活
        """
        ...

    async def get_screenshot(
        self,
        agent_id: str,
        full_page: bool = False
    ) -> Optional[str]:
        """
        获取屏幕截图

        Args:
            agent_id: Agent ID
            full_page: 是否截取整个页面

        Returns:
            截图文件路径
        """
        ...

    async def get_logs(self, agent_id: str, lines: int = 100) -> List[str]:
        """
        获取 Agent 日志

        Args:
            agent_id: Agent ID
            lines: 获取行数

        Returns:
            日志行列表
        """
        ...
