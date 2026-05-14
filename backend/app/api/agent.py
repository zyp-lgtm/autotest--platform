"""
Agent 管理 API - WebSocket 端点

用于管理连接的本地 Agent，并下发测试任务
"""
import logging
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """管理 WebSocket 连接（单例模式）"""

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # 只初始化一次
        if self._initialized:
            return

        # agent_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # agent_id -> agent_info
        self.agents: Dict[str, dict] = {}
        # task_id -> task_result (用于等待执行结果)
        self.task_results: Dict[str, dict] = {}
        # task_id -> event (用于通知等待的协程)
        self.task_events: Dict[str, asyncio.Event] = {}
        # task_id -> event (取消信号)
        self.cancel_events: Dict[str, asyncio.Event] = {}
        self._initialized = True

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
        """获取所有活跃 Agent（只返回 WebSocket 连接正常的）"""
        return {
            agent_id: info
            for agent_id, info in self.agents.items()
            if agent_id in self.active_connections
        }

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

    def set_task_result(self, task_id: str, result: dict):
        """设置任务执行结果"""
        self.task_results[task_id] = result
        # 通知等待的协程
        if task_id in self.task_events:
            self.task_events[task_id].set()
        logger.info(f"任务结果已存储: {task_id}")

    async def wait_for_task_result(self, task_id: str, timeout: float = 30.0) -> Optional[dict]:
        """等待任务执行结果，支持取消信号。真实结果优先于取消信号"""
        event = asyncio.Event()
        self.task_events[task_id] = event

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            # 真实结果优先：如果 agent 已返回结果，忽略取消信号
            real_result = self.task_results.get(task_id)
            if real_result is not None:
                # 清理取消标记
                if task_id in self.cancel_events:
                    del self.cancel_events[task_id]
                return real_result
            # 无真实结果，检查是否被取消
            if self.is_cancelled(task_id):
                return {"cancelled": True}
            return None
        except asyncio.TimeoutError:
            logger.warning(f"等待任务结果超时: {task_id}")
            if self.is_cancelled(task_id):
                return {"cancelled": True}
            return None
        finally:
            if task_id in self.task_events:
                del self.task_events[task_id]

    def clear_task_result(self, task_id: str):
        """清理任务结果"""
        if task_id in self.task_results:
            del self.task_results[task_id]

    def cancel_execution(self, task_execution_id: str):
        """设置取消信号，通知 wait_for_task_result 立即返回"""
        if task_execution_id in self.task_events:
            self.task_events[task_execution_id].set()
        self.cancel_events[task_execution_id] = asyncio.Event()
        self.cancel_events[task_execution_id].set()
        logger.info(f"取消信号已设置: {task_execution_id}")

    def is_cancelled(self, task_execution_id: str) -> bool:
        """检查任务是否已被取消"""
        event = self.cancel_events.get(task_execution_id)
        return event is not None and event.is_set()


# 全局连接管理器
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点（含心跳保活 + 断连检测）"""
    await websocket.accept()
    agent_id = None
    heartbeat_task = None

    async def send_heartbeat():
        """每30秒发送 ping，保持连接存活"""
        while True:
            await asyncio.sleep(30)
            try:
                await websocket.send_json({"type": "ping"})
            except Exception:
                break

    try:
        # 启动心跳
        heartbeat_task = asyncio.create_task(send_heartbeat())

        # 持续监听消息
        while True:
            message = await websocket.receive()

            # 处理文本消息
            if "text" in message:
                try:
                    data = json.loads(message["text"])

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
                        agent_id_from_msg = data.get("agent_id")
                        result = data.get("result")
                        logger.info(f"收到任务结果: task_id={task_id}, agent_id={agent_id_from_msg}, result={result}")

                        # 存储任务结果，供等待的执行器使用
                        if task_id:
                            manager.set_task_result(task_id, {
                                "agent_id": agent_id_from_msg,
                                "result": result
                            })

                    elif data.get("type") == "pong":
                        # 心跳响应
                        pass

                except json.JSONDecodeError:
                    logger.error(f"无效的 JSON 消息: {message}")
                except Exception as e:
                    logger.error(f"处理消息错误: {e}")

            # 处理 WebSocket 关闭
            elif message.get("type") == "websocket.disconnect":
                code = message.get("code", "未知")
                reason = message.get("reason", "无")
                logger.warning(f"Agent {agent_id} WebSocket 断开: code={code}, reason={reason}")
                break

    except WebSocketDisconnect as e:
        logger.warning(f"Agent {agent_id} WebSocket 断开: code={e.code}, reason={e.reason}")
    except Exception as e:
        logger.error(f"Agent {agent_id} WebSocket 错误: {type(e).__name__}: {e}")
    finally:
        # 取消心跳
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

        if agent_id:
            # 通知等待中的任务：Agent 已断连
            for task_id, event in list(manager.task_events.items()):
                if not event.is_set():
                    logger.warning(f"Agent {agent_id} 断连，取消等待中的任务: {task_id}")
                    manager.set_task_result(task_id, {
                        "agent_id": agent_id,
                        "result": {
                            "success": False,
                            "error": f"Agent {agent_id} 连接断开，任务中断"
                        }
                    })
            manager.disconnect(agent_id)
