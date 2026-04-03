"""
Agent 管理 API

用于查看已连接的 Agent 并下发测试任务
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..api import agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


class TaskRequest(BaseModel):
    """下发任务请求"""
    agent_id: str
    task_id: str
    browser_type: str = "chromium"
    headless: bool = False
    url: Optional[str] = None
    steps: List[Dict[str, Any]] = []


@router.get("")
async def list_agents():
    """获取所有已连接的 Agent"""
    agents = agent.manager.get_all_agents()
    return {
        "agents": agents,
        "count": len(agents)
    }


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """获取指定 Agent 信息"""
    agent_info = agent.manager.get_agent(agent_id)
    if not agent_info:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return agent_info


@router.post("/dispatch")
async def dispatch_task(request: TaskRequest):
    """下发任务给指定 Agent"""
    agent_info = agent.manager.get_agent(request.agent_id)
    if not agent_info:
        raise HTTPException(status_code=404, detail="Agent 不存在或未连接")

    # 构建任务消息
    task_message = {
        "type": "task",
        "task_id": request.task_id,
        "browser_type": request.browser_type,
        "headless": request.headless,
        "url": request.url,
        "steps": request.steps
    }

    # 发送给 Agent
    success = await agent.manager.send_to_agent(request.agent_id, task_message)

    if not success:
        raise HTTPException(status_code=500, detail="发送任务失败")

    return {
        "success": True,
        "message": "任务已下发",
        "agent_id": request.agent_id,
        "task_id": request.task_id
    }


@router.post("/{agent_id}/close")
async def close_browser(agent_id: str):
    """关闭 Agent 的浏览器"""
    agent_info = agent.manager.get_agent(agent_id)
    if not agent_info:
        raise HTTPException(status_code=404, detail="Agent 不存在或未连接")

    await agent.manager.send_to_agent(agent_id, {"type": "close"})

    return {
        "success": True,
        "message": "已发送关闭浏览器命令"
    }
