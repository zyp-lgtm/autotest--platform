"""
Agent 管理 API - WebSocket 端点

用于管理连接的本地 Agent，并下发测试任务
"""
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """管理 WebSocket 连接"""

    def __init__(self):
        # agent_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # agent_id -> agent_info
        self.agents: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, agent_id: str):
        """接受连接"""
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        logger.info(f"Agent 已连接: {agent_id}")

    def disconnect(self, agent_id: str):
        """断开连接"""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
        if agent_id in self.agents:
            del self.agents[agent_id]
        logger.info(f"Agent 已断开: {agent_id}")

    def register_agent(self, agent_id: str, agent_info: dict):
        """注册 Agent"""
        self.agents[agent_id] = {
            **agent_info,
            "connected_at": datetime.now().isoformat()
        }
        logger.info(f"Agent 已注册: {agent_id} - {agent_info}")

    def get_agent(self, agent_id: str) -> dict:
        """获取 Agent 信息"""
        return self.agents.get(agent_id)

    def get_all_agents(self) -> Dict[str, dict]:
        """获取所有 Agent"""
        return self.agents

    async def send_to_agent(self, agent_id: str, message: dict):
        """发送消息给指定 Agent"""
        if agent_id in self.active_connections:
            websocket = self.active_connections[agent_id]
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.error(f"发送消息失败 ({agent_id}): {e}")
                return False
        return False

    async def broadcast(self, message: dict):
        """广播消息给所有 Agent"""
        for agent_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败 ({agent_id}): {e}")


# 全局连接管理器
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点"""
    await websocket.accept()
    agent_id = None

    try:
        async for message in websocket:
            data = json.loads(message)

            if data.get("type") == "register":
                # 注册 Agent
                agent_id = data.get("agent_id") or str(uuid.uuid4())
                manager.register_agent(agent_id, data.get("capabilities", {}))
                manager.active_connections[agent_id] = websocket

                # 发送确认
                await websocket.send_json({
                    "type": "registered",
                    "agent_id": agent_id,
                    "message": "Agent 已注册"
                })

                logger.info(f"Agent 已注册: {agent_id}")

            elif data.get("type") == "task_result":
                # 接收任务结果
                task_id = data.get("task_id")
                result = data.get("result")
                logger.info(f"收到任务结果: {task_id} - {result}")

                # TODO: 保存到数据库
                # 这里可以更新执行记录的状态

            elif data.get("type") == "pong":
                # 心跳响应
                pass

    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开: {agent_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
    finally:
        if agent_id:
            manager.disconnect(agent_id)
