"""
录制管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from ...core.database import get_db
from ...models.user import User
from ...core.security import get_authenticated_user
from ..utils import validate_and_fetch

from ...services.recorder import browser_recorder, CapturedAction
from ...services.recording.converter import recording_converter, GeneratedScenario
from ...services.recording.data_extractor import data_extractor, DataPattern

router = APIRouter(prefix="/recording", tags=["录制管理"])


# Pydantic 模型
class RecordingStartRequest(BaseModel):
    project_id: str
    scenario_name: str


class RecordingStopRequest(BaseModel):
    session_id: str


class DataExtractionRequest(BaseModel):
    actions: List[Dict[str, Any]]


class ScenarioGenerationRequest(BaseModel):
    project_id: str
    scenario_name: str
    actions: List[Dict[str, Any]]
    data_patterns: List[Dict[str, Any]]


@router.post("/start")
async def start_recording(
    request: RecordingStartRequest,
    user: User = Depends(get_authenticated_user)
):
    """启动录制会话"""
    try:
        session_id = await browser_recorder.start_session(
            project_id=request.project_id,
            scenario_name=request.scenario_name
        )

        return {
            "session_id": session_id,
            "status": "recording",
            "message": "录制已启动，请在浏览器中执行您的测试操作",
            "instructions": {
                "browser_launched": "录制浏览器已打开",
                "start_operations": "在地址栏输入测试网页URL并执行操作",
                "monitoring": "系统会自动捕获您的操作",
                "stop_recording": "完成后在控制台输入 stopRecording() 或返回此页面停止"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动录制失败: {str(e)}")


@router.post("/stop")
async def stop_recording(
    request: RecordingStopRequest,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """停止录制并返回捕获的操作"""
    try:
        result = await browser_recorder.stop_session(request.session_id)

        return {
            "session_id": request.session_id,
            "actions_count": result["actions_count"],
            "actions": result["actions"],
            "scenario_name": result["scenario_name"],
            "project_id": result["project_id"],
            "status": "processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止录制失败: {str(e)}")


@router.get("/actions/{session_id}")
async def get_captured_actions(
    session_id: str,
    user: User = Depends(get_authenticated_user)
):
    """实时获取捕获的操作（用于前端轮询）"""
    try:
        actions = await browser_recorder.get_captured_actions(session_id)

        return {
            "session_id": session_id,
            "actions": actions,
            "actions_count": len(actions),
            "timestamp": int(__import__('time').time())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取操作失败: {str(e)}")


@router.post("/extract-data")
async def extract_test_data(
    request: DataExtractionRequest,
    user: User = Depends(get_authenticated_user)
):
    """智能提取测试数据"""
    try:
        # 转换为 CapturedAction 对象
        actions = [
            CapturedAction(**action) for action in request.actions
        ]

        # 提取数据模式
        patterns = data_extractor.extract_patterns(actions)

        return {
            "patterns": [
                {
                    "id": p.id,
                    "field_name": p.field_name,
                    "pattern_type": p.pattern_type,
                    "values": p.values,
                    "confidence": p.confidence,
                    "selected": p.selected,
                    "suggested_variations": p.suggested_variations
                }
                for p in patterns
            ],
            "patterns_count": len(patterns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据提取失败: {str(e)}")


@router.post("/generate-scenario")
async def generate_scenario(
    request: ScenarioGenerationRequest,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """从录制数据生成测试场景"""
    try:
        # 转换操作和模式
        actions = [
            CapturedAction(**action) for action in request.actions
        ]

        patterns = [
            DataPattern(**pattern) for pattern in request.data_patterns
        ]

        # 生成场景
        scenario = await recording_converter.convert_to_scenario(
            actions=actions,
            scenario_name=request.scenario_name,
            project_id=request.project_id
        )

        # 生成测试数据（如果有选择的模式）
        test_data = None
        if patterns:
            test_data = data_extractor.generate_test_data(
                patterns=patterns,
                scenario_name=request.scenario_name,
                project_id=request.project_id
            )

        return {
            "scenario": {
                "name": scenario.name,
                "description": scenario.description,
                "scenario_type": scenario.scenario_type,
                "cases": [
                    {
                        "id": case.id,
                        "name": case.name,
                        "description": case.description,
                        "steps": [
                            {
                                "id": step.id,
                                "step_name": step.step_name,
                                "keyword_id": step.keyword_id,
                                "parameters": step.parameters,
                                "enabled": step.enabled,
                                "continue_on_failure": step.continue_on_failure,
                                "step_order": step.step_order
                            }
                            for step in case.steps
                        ]
                    }
                    for case in scenario.cases
                ],
                "metadata": {
                    "created_by": "recording",
                    "actions_count": len(actions),
                    "data_patterns_count": len(patterns)
                }
            },
            "test_data": test_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成场景失败: {str(e)}")


@router.get("/sessions")
async def list_sessions(
    user: User = Depends(get_authenticated_user)
):
    """列出所有活动的录制会话"""
    try:
        sessions = list(browser_recorder.sessions.values())

        return {
            "sessions": [
                {
                    "id": session.id,
                    "project_id": session.project_id,
                    "scenario_name": session.scenario_name,
                    "status": session.status,
                    "actions_count": len(session.captured_actions),
                    "started_at": session.started_at.isoformat() if session.started_at else None
                }
                for session in sessions
            ],
            "sessions_count": len(sessions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.post("/sessions/{session_id}/close")
async def close_session(
    session_id: str,
    user: User = Depends(get_authenticated_user)
):
    """关闭录制会话并清理资源"""
    try:
        await browser_recorder.close_session(session_id)

        return {
            "message": "录制会话已关闭",
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"关闭会话失败: {str(e)}")


@router.get("/health")
async def health_check():
    """录制服务健康检查"""
    return {
        "status": "healthy",
        "active_sessions": len(browser_recorder.sessions),
        "available": True
    }