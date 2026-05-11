"""
录制管理 API
"""
import uuid
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

from ..core.database import get_db
from ..models.user import User
from ..models.ui_task import UITask
from ..core.security import get_authenticated_user
from .utils import validate_and_fetch
from ..utils.cache import invalidate_pattern

from ..services.recorder import browser_recorder, CapturedAction
from ..services.recording.converter import recording_converter, GeneratedScenario
from ..services.recording.data_extractor import data_extractor, DataPattern

router = APIRouter(prefix="/recording", tags=["录制管理"])


# Pydantic 模型
class RecordingConfig(BaseModel):
    enableSmartWait: bool = True
    autoExtractVariables: bool = True
    mergeContinuousInputs: bool = True


class RecordingStartRequest(BaseModel):
    project_id: str
    scenario_name: str
    config: Optional[RecordingConfig] = None


class RecordingStopRequest(BaseModel):
    session_id: str


class DataExtractionRequest(BaseModel):
    actions: List[Dict[str, Any]]


class ScenarioGenerationRequest(BaseModel):
    project_id: str
    scenario_name: str
    actions: List[Dict[str, Any]]
    data_patterns: List[Dict[str, Any]]
    config: Optional[RecordingConfig] = None


@router.post("/start")
async def start_recording(
    request: RecordingStartRequest,
    user: User = Depends(get_authenticated_user)
):
    """启动录制会话"""
    try:
        # 合并配置，使用默认值如果未提供
        config = request.config or RecordingConfig()

        session_id = await browser_recorder.start_session(
            project_id=request.project_id,
            scenario_name=request.scenario_name,
            config=config
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
    """从录制数据生成测试场景（支持变量替换）"""
    try:
        # 转换操作和模式
        actions = [
            CapturedAction(**action) for action in request.actions
        ]

        patterns = [
            DataPattern(**pattern) for pattern in request.data_patterns
        ]

        # 🔥 提取选中的模式ID
        selected_pattern_ids = [
            p.id for p in patterns if p.selected
        ]

        # 生成场景
        config = request.config or RecordingConfig()
        scenario = await recording_converter.convert_to_scenario(
            actions=actions,
            scenario_name=request.scenario_name,
            project_id=request.project_id,
            enable_smart_wait=config.enableSmartWait,
            data_patterns=patterns,  # 🔥 传递数据模式
            selected_patterns=selected_pattern_ids,  # 🔥 传递选中的模式
            filter_auto_navigate=True  # 🔥 智能过滤：只保留主动导航，过滤自动跳转
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
    except NameError as ne:
        # 捕获NameError并输出详细信息
        import traceback
        import sys
        print(f"❌ NameError: {ne}", file=sys.stderr)
        print(f"Traceback:\n{traceback.format_exc()}", file=sys.stderr)
        error_detail = f"NameError: {str(ne)}\n\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)
    except Exception as e:
        import traceback
        import sys
        print(f"❌ Exception: {e}", file=sys.stderr)
        print(f"Traceback:\n{traceback.format_exc()}", file=sys.stderr)
        error_detail = f"生成场景失败: {str(e)}\n\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


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


class SaveScenarioRequest(BaseModel):
    """保存录制的场景请求"""
    task_id: str
    project_id: str
    scenario_name: str
    scenario_description: str
    scenario_type: str
    cases: List[Dict[str, Any]]
    test_data: Optional[Dict[str, Any]] = None  # 添加测试数据字段


@router.post("/save-scenario")
async def save_recorded_scenario(
    request: SaveScenarioRequest,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """保存录制的场景到数据库"""
    try:
        from ..models.ui_task import UIScenario, UICase, UIStep
        from ..models.keyword import Keyword
        from ..models.test_data import TestData, DataBinding

        # 验证 task_id 和获取任务信息
        task = validate_and_fetch(db, UITask, request.task_id, "任务")

        # 验证 project_id
        try:
            project_id_uuid = uuid.UUID(request.project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的项目ID格式")

        if task.project_id != project_id_uuid:
            raise HTTPException(status_code=400, detail="项目ID不匹配")

        # 验证并转换 task_id
        task_id_uuid = uuid.UUID(request.task_id)

        # 保存测试数据（如果有）
        test_data_id = None
        if request.test_data and request.test_data.get("data"):
            test_data_record = TestData(
                project_id=project_id_uuid,
                name=request.test_data.get("name", f"{request.scenario_name}_测试数据"),
                description=request.test_data.get("description", f"从录制自动生成"),
                data_type="json",
                data=request.test_data.get("data", []),
                tags=request.test_data.get("tags", ["recording", "auto-generated"]),
                created_by=user.id
            )
            db.add(test_data_record)
            db.flush()  # 获取 test_data.id
            test_data_id = test_data_record.id
            logger.info(f"创建测试数据: {test_data_record.name} (ID: {test_data_id})")

        # 创建场景
        # 🔥 获取当前最大的执行顺序
        from sqlalchemy import func
        max_order = db.query(func.max(UIScenario.execution_order)).filter(
            UIScenario.task_id == task_id_uuid
        ).scalar() or -1

        scenario = UIScenario(
            task_id=task_id_uuid,
            project_id=project_id_uuid,
            name=request.scenario_name,
            description=request.scenario_description,
            scenario_type=request.scenario_type,
            execution_order=max_order + 1,  # 🔥 设置为最大值+1
            case_ids=[],
            tags=[]
        )
        db.add(scenario)
        db.flush()  # 获取 scenario.id

        # 创建用例和步骤
        case_ids = []
        for case_data in request.cases:
            # 创建用例
            ui_case = UICase(
                project_id=project_id_uuid,
                scenario_id=scenario.id,
                name=case_data["name"],
                description=case_data.get("description", ""),
                case_type="ui",
                step_ids=[],
                priority="medium",
                tags=[],
                data_bindings={},
                browser_config={}
            )
            db.add(ui_case)
            db.flush()  # 获取 case.id

            # 创建步骤
            step_ids = []
            total_steps = len(case_data.get("steps", []))
            skipped_steps = 0
            for step_data in case_data.get("steps", []):
                # 跳过没有 keyword_id 的步骤（这些是自动生成的断言步骤，尚未实现）
                if not step_data.get("keyword_id"):
                    skipped_steps += 1
                    continue

                # 查找关键字ID（从名称映射到ID）
                keyword_name = step_data["keyword_id"].replace("kw_", "")
                keyword = db.query(Keyword).filter(
                    Keyword.name == keyword_name
                ).first()

                print(f"DEBUG: 处理步骤: keyword_name={keyword_name}, found={keyword is not None}")

                if not keyword:
                    # 如果关键字不存在，使用默认关键字
                    keyword = db.query(Keyword).filter(Keyword.name == "CLICK").first()
                    if not keyword:
                        raise HTTPException(
                            status_code=400,
                            detail=f"关键字 {keyword_name} 不存在"
                        )

                step = UIStep(
                    case_id=ui_case.id,
                    scenario_id=scenario.id,
                    task_id=task_id_uuid,
                    step_order=step_data["step_order"],
                    keyword_id=keyword.id,
                    step_name=step_data["step_name"],
                    step_type="action",
                    parameters=step_data.get("parameters", {}),
                    enabled=step_data.get("enabled", True),
                    continue_on_failure=step_data.get("continue_on_failure", False),
                    screenshot_config={}
                )
                db.add(step)
                db.flush()  # 立即flush以获取step.id
                step_ids.append(str(step.id))

            print(f"DEBUG: 用例 {case_data['name']}: 总步骤={total_steps}, 跳过={skipped_steps}, 保存={len(step_ids)}")

            # 更新用例的 step_ids
            ui_case.step_ids = step_ids

            # 如果有测试数据，创建数据绑定
            if test_data_id:
                binding = DataBinding(
                    case_id=ui_case.id,
                    data_id=test_data_id,
                    enabled=1
                )
                db.add(binding)
                logger.info(f"创建数据绑定: 用例 {ui_case.name} -> 测试数据 {test_data_id}")

            # SQLite 存储 UUID 时会自动去除横线，保持一致
            case_ids.append(str(ui_case.id).replace('-', ''))

        # 更新场景的 case_ids
        scenario.case_ids = case_ids

        # 更新任务的 scenario_ids
        # 使用原生 SQL 直接更新，避免 ORM 会话问题
        from sqlalchemy import text

        # SQLite 存储的 UUID 没有横线，需要去除横线
        task_id_str = str(task_id_uuid).replace('-', '')
        scenario_id_str = str(scenario.id).replace('-', '')

        logger.info(f"DEBUG: 准备更新任务 {task_id_uuid} 的 scenario_ids，添加场景 {scenario_id_str}")

        # 先查询当前的 scenario_ids
        result = db.execute(
            text("SELECT scenario_ids FROM ui_tasks WHERE id = :task_id"),
            {"task_id": task_id_str}
        )
        row = result.fetchone()

        if row:
            current_ids_json = row[0]
            logger.info(f"DEBUG: 当前 scenario_ids (原始): {current_ids_json}")

            # 解析 JSON
            try:
                if isinstance(current_ids_json, str):
                    current_ids = json.loads(current_ids_json)
                else:
                    current_ids = current_ids_json if current_ids_json else []
            except Exception as e:
                logger.info(f"DEBUG: JSON 解析失败: {e}，使用空列表")
                current_ids = []

            # 确保是列表
            if not isinstance(current_ids, list):
                current_ids = []

            logger.info(f"DEBUG: 解析后的 scenario_ids: {current_ids}")

            # 添加新场景 ID
            if scenario_id_str not in current_ids:
                current_ids.append(scenario_id_str)
                new_ids_json = json.dumps(current_ids)

                logger.info(f"DEBUG: 准备更新为: {new_ids_json}")

                # 使用原生 SQL 直接更新
                update_result = db.execute(
                    text("UPDATE ui_tasks SET scenario_ids = :scenario_ids WHERE id = :task_id"),
                    {"scenario_ids": new_ids_json, "task_id": task_id_str}
                )

                logger.info(f"DEBUG: 更新行数: {update_result.rowcount}")

                # 立即提交
                db.commit()
                logger.info(f"DEBUG: 数据库已提交")

                # 验证更新
                verify_result = db.execute(
                    text("SELECT scenario_ids FROM ui_tasks WHERE id = :task_id"),
                    {"task_id": task_id_str}
                )
                verify_row = verify_result.fetchone()
                logger.info(f"DEBUG: 验证查询结果: {verify_row[0] if verify_row else 'None'}")
            else:
                logger.info(f"DEBUG: 场景 ID 已存在，跳过")
        else:
            logger.info(f"DEBUG: 未找到任务 {task_id_uuid}")

        # 一次性提交所有更改（如果还没有提交）
        db.commit()
        logger.info(f"DEBUG: 最终提交完成")

        # 🔥 清除场景列表缓存
        try:
            invalidate_pattern("list_scenarios*")
            logger.info(f"已清除场景列表缓存")
        except Exception as e:
            logger.warning(f"清除缓存失败: {e}")

        # 重新加载场景数据以返回完整信息
        db.refresh(scenario)

        # 🔥 确保 case_ids 返回正确的格式（处理 JSON 字符串情况）
        case_ids = scenario.case_ids
        if isinstance(case_ids, str):
            try:
                case_ids = json.loads(case_ids)
            except:
                case_ids = []

        return {
            "id": str(scenario.id),
            "task_id": str(scenario.task_id),
            "project_id": str(scenario.project_id),
            "name": scenario.name,
            "description": scenario.description,
            "scenario_type": scenario.scenario_type,
            "execution_order": scenario.execution_order,
            "case_ids": case_ids,
            "tags": list(scenario.tags) if scenario.tags else [],
            "created_at": scenario.created_at.isoformat() if scenario.created_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        raise HTTPException(
            status_code=500,
            detail=f"保存场景失败: {str(e)}\n\n{traceback.format_exc()}"
        )