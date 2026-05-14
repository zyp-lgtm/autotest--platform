"""
场景管理 API
提供场景、用例、步骤的 CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid
import json

from ...models.ui_task import UITask, UIScenario, UICase, UIStep
from ...models.keyword import Keyword
from ...models.user import User
from ...schemas.scenario import ScenarioCreate, ScenarioUpdate, ScenarioResponse
from ...schemas.case import CaseCreate, CaseUpdate, CaseResponse
from ...schemas.step import StepCreate, StepUpdate, StepResponse
from ...core.database import get_db
from ...core.security import get_authenticated_user
from ...utils.cache import cache_response, invalidate_pattern
from ..utils import validate_and_fetch, validate_uuid, serialize_model
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ui/scenarios", tags=["场景管理"])


def append_to_json_ids_field(obj, field_name, value):
    """
    安全地追加值到 JSON *_ids 字段

    SQLite 的 JSON 字段可能返回字符串或列表
    这个函数处理两种情况并确保返回正确的列表格式
    """
    import json

    # 获取当前值
    current_value = getattr(obj, field_name)

    # 如果是字符串，尝试解析为 JSON
    if isinstance(current_value, str):
        try:
            current_value = json.loads(current_value)
        except:
            current_value = []
    # 如果是 None 或其他类型，初始化为空列表
    elif not isinstance(current_value, list):
        current_value = []

    # 追加新值
    current_value.append(value)

    # 更新对象
    setattr(obj, field_name, current_value)

router = APIRouter(prefix="/ui/scenarios", tags=["场景管理"])


@router.post("/")
@router.post("")
async def create_scenario(
    scenario: ScenarioCreate,
    task_id: str = Query(..., description="任务ID"),
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """创建场景"""
    try:
        # 验证并转换 UUID
        task_id_uuid = validate_uuid(task_id, "任务")

        # 验证任务存在
        task = validate_and_fetch(db, UITask, task_id, "任务")

        # 获取当前最大执行顺序
        max_order = db.query(UIScenario).filter(
            UIScenario.task_id == task_id_uuid
        ).count()

        # 创建场景（使用 UUID 对象，SQLAlchemy 会自动处理）
        new_scenario = UIScenario(
            name=scenario.name,
            description=scenario.description,
            scenario_type=scenario.scenario_type,
            tags=scenario.tags or [],
            task_id=task_id_uuid,  # UUID 对象
            project_id=task.project_id,  # UUID 对象
            execution_order=max_order,
            case_ids=[]
        )
        db.add(new_scenario)
        db.commit()
        db.refresh(new_scenario)

        # 更新任务的场景列表
        append_to_json_ids_field(task, 'scenario_ids', str(new_scenario.id))
        db.commit()

        # 清除场景列表缓存
        try:
            invalidate_pattern("list_scenarios*")
        except Exception as e:
            logger.warning(f"清除缓存失败: {e}")

        # 手动序列化
        return {
            "id": str(new_scenario.id),
            "task_id": str(new_scenario.task_id),
            "project_id": str(new_scenario.project_id),
            "name": new_scenario.name,
            "description": new_scenario.description,
            "scenario_type": new_scenario.scenario_type,
            "execution_order": new_scenario.execution_order,
            "case_ids": [str(cid) for cid in (new_scenario.case_ids or [])],
            "tags": list(new_scenario.tags) if new_scenario.tags else [],
            "created_at": new_scenario.created_at.isoformat() if new_scenario.created_at else None,
            "updated_at": new_scenario.updated_at.isoformat() if new_scenario.updated_at else None
        }
    except Exception as e:
        logger.error(f"创建场景失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"创建场景失败: {str(e)}"
        )


@router.get("/")
@router.get("")
@cache_response(ttl=300)  # 缓存 5 分钟
async def list_scenarios(
    task_id: str = Query(..., description="任务ID"),
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取任务的所有场景"""
    task_id_uuid = validate_uuid(task_id, "任务")

    scenarios = db.query(UIScenario).filter(
        UIScenario.task_id == task_id_uuid
    ).order_by(UIScenario.execution_order).all()

    result = []
    for scenario in scenarios:
        result.append(serialize_model(scenario))
    return result


@router.get("/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取场景详情"""
    scenario = validate_and_fetch(db, UIScenario, scenario_id, "场景")
    return serialize_model(scenario)


@router.put("/{scenario_id}")
async def update_scenario(
    scenario_id: str,
    scenario_update: ScenarioUpdate,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """更新场景"""
    scenario = validate_and_fetch(db, UIScenario, scenario_id, "场景")

    update_data = scenario_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scenario, field, value)

    db.commit()
    db.refresh(scenario)

    return serialize_model(scenario)


@router.delete("/{scenario_id}")
async def delete_scenario(
    scenario_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """删除场景"""
    try:
        # 验证并转换 UUID
        scenario_id_uuid = validate_uuid(scenario_id, "场景")

        # 验证场景存在
        scenario = validate_and_fetch(db, UIScenario, scenario_id, "场景")

        task_id = scenario.task_id

        # 级联删除：先删除步骤，再删除用例，最后删除场景
        # 1. 获取并删除所有用例
        cases = db.query(UICase).filter(UICase.scenario_id == scenario_id_uuid).all()

        for case in cases:
            # 删除用例的所有步骤
            db.query(UIStep).filter(UIStep.case_id == case.id).delete()
            # 删除用例
            db.delete(case)

        # 2. 删除场景
        db.delete(scenario)
        db.commit()

        # 更新任务的场景列表
        task = db.query(UITask).filter(UITask.id == task_id).first()
        if task and task.scenario_ids:
            import json
            # 确保 scenario_ids 是列表
            if isinstance(task.scenario_ids, str):
                try:
                    scenario_ids_list = json.loads(task.scenario_ids)
                except:
                    scenario_ids_list = []
            else:
                scenario_ids_list = task.scenario_ids

            # 移除删除的场景 ID
            task.scenario_ids = [sid for sid in scenario_ids_list if sid != str(scenario_id_uuid)]
            db.commit()

        # 清除场景列表缓存 - 🔥 修复缓存问题
        try:
            invalidate_pattern("list_scenarios*")
            logger.info(f"已清除场景列表缓存，删除场景: {scenario_id}")
        except Exception as e:
            logger.warning(f"清除缓存失败: {e}")

        return {"message": "场景已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除场景失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"删除场景失败: {str(e)}"
        )


# ==================== 用例管理 ====================

@router.post("/{scenario_id}/cases")
async def create_case(
    scenario_id: str,
    case: CaseCreate,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """创建用例"""
    try:
        # 验证并转换 UUID
        scenario_id_uuid = validate_uuid(scenario_id, "场景")

        # 验证场景存在
        scenario = validate_and_fetch(db, UIScenario, scenario_id, "场景")

        # 创建用例（使用 UUID 对象）
        new_case = UICase(
            name=case.name,
            description=case.description,
            case_type=case.case_type,
            priority=case.priority,
            tags=case.tags or [],
            data_bindings=case.data_bindings or {},
            browser_config=case.browser_config or {},
            scenario_id=scenario_id_uuid,
            project_id=scenario.project_id,
            step_ids=[]
        )
        db.add(new_case)
        db.commit()
        db.refresh(new_case)

        # 更新场景的用例列表
        append_to_json_ids_field(scenario, 'case_ids', str(new_case.id))
        db.commit()

        # 手动序列化
        return {
            "id": str(new_case.id),
            "scenario_id": str(new_case.scenario_id),
            "project_id": str(new_case.project_id),
            "name": new_case.name,
            "description": new_case.description,
            "case_type": new_case.case_type,
            "step_ids": [str(sid) for sid in (new_case.step_ids or [])],
            "priority": new_case.priority,
            "tags": list(new_case.tags) if new_case.tags else [],
            "data_bindings": new_case.data_bindings or {},
            "browser_config": new_case.browser_config or {},
            "created_at": new_case.created_at.isoformat() if new_case.created_at else None,
            "updated_at": new_case.updated_at.isoformat() if new_case.updated_at else None
        }
    except Exception as e:
        logger.error(f"创建用例失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"创建用例失败: {str(e)}"
        )

    # 更新场景的用例列表（将 UUID 转换为字符串以支持 JSON 序列化）
    if not scenario.case_ids:
        scenario.case_ids = []
    scenario.case_ids.append(str(new_case.id))
    db.commit()

    # 手动序列化
    return {
        "id": str(new_case.id),
        "scenario_id": str(new_case.scenario_id),
        "project_id": str(new_case.project_id),
        "name": new_case.name,
        "description": new_case.description,
        "case_type": new_case.case_type,
        "step_ids": [str(sid) for sid in (new_case.step_ids or [])],
        "priority": new_case.priority,
        "tags": list(new_case.tags) if new_case.tags else [],
        "data_bindings": new_case.data_bindings or {},
        "browser_config": new_case.browser_config or {},
        "created_at": new_case.created_at.isoformat() if new_case.created_at else None,
        "updated_at": new_case.updated_at.isoformat() if new_case.updated_at else None
    }


@router.get("/{scenario_id}/cases")
async def list_cases(
    scenario_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取场景的所有用例"""
    scenario_id_uuid = validate_uuid(scenario_id, "场景")

    cases = db.query(UICase).filter(UICase.scenario_id == scenario_id_uuid).all()

    result = []
    for case_item in cases:
        result.append(serialize_model(case_item))
    return result


@router.put("/cases/{case_id}")
async def update_case(
    case_id: str,
    case_update: CaseUpdate,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """更新用例"""
    case_item = validate_and_fetch(db, UICase, case_id, "用例")

    update_data = case_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case_item, field, value)

    db.commit()
    db.refresh(case_item)

    return serialize_model(case_item)


@router.delete("/cases/{case_id}")
async def delete_case(
    case_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """删除用例"""
    try:
        # 验证并转换 UUID
        case_id_uuid = validate_uuid(case_id, "用例")

        # 验证用例存在
        case_item = validate_and_fetch(db, UICase, case_id, "用例")

        scenario_id = case_item.scenario_id

        # 级联删除：先删除步骤，再删除用例
        # 1. 删除用例的所有步骤
        db.query(UIStep).filter(UIStep.case_id == case_id_uuid).delete()

        # 2. 删除用例
        db.delete(case_item)
        db.commit()

        # 更新场景的用例列表
        scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id).first()
        if scenario and scenario.case_ids:
            import json
            # 确保 case_ids 是列表
            if isinstance(scenario.case_ids, str):
                try:
                    case_ids_list = json.loads(scenario.case_ids)
                except:
                    case_ids_list = []
            else:
                case_ids_list = scenario.case_ids

            # 移除删除的用例 ID
            scenario.case_ids = [cid for cid in case_ids_list if cid != str(case_id_uuid)]
            db.commit()

        # 清除用例列表缓存 - 🔥 修复缓存问题
        try:
            invalidate_pattern("list_cases*")
            logger.info(f"已清除用例列表缓存，删除用例: {case_id}")
        except Exception as e:
            logger.warning(f"清除缓存失败: {e}")

        return {"message": "用例已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用例失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"删除用例失败: {str(e)}"
        )


# ==================== 步骤管理 ====================

@router.post("/cases/{case_id}/steps")
async def create_step(
    case_id: str,
    step: StepCreate,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """创建步骤"""
    try:
        # 验证并转换 UUID
        case_id_uuid = validate_uuid(case_id, "用例")

        # 验证用例存在
        case_item = validate_and_fetch(db, UICase, case_id, "用例")

        # 获取场景和任务信息
        scenario = db.query(UIScenario).filter(UIScenario.id == case_item.scenario_id).first()
        if not scenario:
            raise HTTPException(status_code=404, detail="场景不存在")

        # 验证关键字存在
        keyword = validate_and_fetch(db, Keyword, str(step.keyword_id), "关键字")

        # 获取当前最大步骤顺序
        max_order = db.query(UIStep).filter(UIStep.case_id == case_id_uuid).count()

        # 创建步骤
        new_step = UIStep(
            keyword_id=validate_uuid(str(step.keyword_id), "关键字"),
            step_name=step.step_name,
            parameters=step.parameters or {},
            enabled=step.enabled if hasattr(step, 'enabled') else True,
            continue_on_failure=step.continue_on_failure if hasattr(step, 'continue_on_failure') else False,
            screenshot_config=step.screenshot_config or {},
            case_id=case_id_uuid,
            scenario_id=case_item.scenario_id,
            task_id=scenario.task_id,
            step_order=max_order,
            step_type=keyword.category
        )
        db.add(new_step)
        db.commit()
        db.refresh(new_step)

        # 更新用例的步骤列表
        append_to_json_ids_field(case_item, 'step_ids', str(new_step.id))
        db.commit()

        # 手动序列化
        return {
            "id": str(new_step.id),
            "case_id": str(new_step.case_id),
            "scenario_id": str(new_step.scenario_id),
            "task_id": str(new_step.task_id),
            "step_order": new_step.step_order,
            "keyword_id": str(new_step.keyword_id),
            "step_name": new_step.step_name,
            "step_type": new_step.step_type,
            "parameters": new_step.parameters or {},
            "enabled": new_step.enabled,
            "continue_on_failure": new_step.continue_on_failure,
            "screenshot_config": new_step.screenshot_config or {},
            "created_at": new_step.created_at.isoformat() if new_step.created_at else None,
            "updated_at": new_step.updated_at.isoformat() if new_step.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建步骤失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"创建步骤失败: {str(e)}"
        )


@router.get("/cases/{case_id}/steps")
async def list_steps(
    case_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取用例的所有步骤"""
    case_id_uuid = validate_uuid(case_id, "用例")

    steps = db.query(UIStep).filter(UIStep.case_id == case_id_uuid).order_by(UIStep.step_order).all()

    result = []
    for step_item in steps:
        result.append(serialize_model(step_item))
    return result


@router.put("/steps/{step_id}")
async def update_step(
    step_id: str,
    step_update: StepUpdate,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """更新步骤"""
    step_item = validate_and_fetch(db, UIStep, step_id, "步骤")

    update_data = step_update.dict(exclude_unset=True)

    # 如果更新了关键字，更新步骤类型
    if 'keyword_id' in update_data:
        keyword = validate_and_fetch(db, Keyword, str(update_data['keyword_id']), "关键字")
        update_data['step_type'] = keyword.category

    for field, value in update_data.items():
        setattr(step_item, field, value)

    db.commit()
    db.refresh(step_item)

    return serialize_model(step_item)


@router.delete("/steps/{step_id}")
async def delete_step(
    step_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """删除步骤"""
    try:
        # 验证并转换 UUID
        step_id_uuid = validate_uuid(step_id, "步骤")

        # 验证步骤存在
        step_item = validate_and_fetch(db, UIStep, step_id, "步骤")

        case_id = step_item.case_id

        db.delete(step_item)
        db.commit()

        # 更新用例的步骤列表
        case_item = db.query(UICase).filter(UICase.id == case_id).first()
        if case_item and case_item.step_ids:
            import json
            # 确保 step_ids 是列表
            if isinstance(case_item.step_ids, str):
                try:
                    step_ids_list = json.loads(case_item.step_ids)
                except:
                    step_ids_list = []
            else:
                step_ids_list = case_item.step_ids

            # 移除删除的步骤 ID
            case_item.step_ids = [sid for sid in step_ids_list if sid != str(step_id_uuid)]
            db.commit()

        # 清除步骤列表缓存 - 🔥 修复缓存问题
        try:
            invalidate_pattern("list_steps*")
            logger.info(f"已清除步骤列表缓存，删除步骤: {step_id}")
        except Exception as e:
            logger.warning(f"清除缓存失败: {e}")

        return {"message": "步骤已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除步骤失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"删除步骤失败: {str(e)}"
        )


class BatchInsertStepsRequest(BaseModel):
    after_step_ids: List[str]
    keyword_name: str
    parameters: dict = {}
    continue_on_failure: bool = True


@router.post("/cases/{case_id}/steps/batch-insert")
async def batch_insert_steps(
    case_id: str,
    request: BatchInsertStepsRequest,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """批量插入步骤——在指定步骤后各插入一个新步骤"""
    try:
        case_id_uuid = validate_uuid(case_id, "用例")
        case_item = validate_and_fetch(db, UICase, case_id, "用例")

        # 验证关键字存在
        keyword = db.query(Keyword).filter(Keyword.name == request.keyword_name).first()
        if not keyword:
            raise HTTPException(status_code=400, detail=f"关键字不存在: {request.keyword_name}")

        scenario = db.query(UIScenario).filter(UIScenario.id == case_item.scenario_id).first()
        if not scenario:
            raise HTTPException(status_code=404, detail="场景不存在")

        # 收集所有 after 步骤并按 step_order 从大到小排序（从后往前插入避免冲突）
        after_steps = []
        for step_id_str in request.after_step_ids:
            step_id = validate_uuid(step_id_str, "步骤")
            step = db.query(UIStep).filter(
                UIStep.id == step_id, UIStep.case_id == case_id_uuid
            ).first()
            if not step:
                raise HTTPException(status_code=400, detail=f"步骤不属于该用例: {step_id_str}")
            after_steps.append(step)

        after_steps.sort(key=lambda s: s.step_order, reverse=True)

        # 提前获取 ASSERT_NO_ERROR 关键字的 ID 用于去重检查
        assert_kw = db.query(Keyword).filter(Keyword.name == "ASSERT_NO_ERROR").first()
        assert_kw_id = assert_kw.id if assert_kw else None

        created_steps = []
        skipped_duplicates = 0
        for after_step in after_steps:
            insert_order = after_step.step_order + 1

            # 去重：检查紧邻的下一步是否已经是 ASSECT_NO_ERROR
            next_step = db.query(UIStep).filter(
                UIStep.case_id == case_id_uuid,
                UIStep.step_order == insert_order
            ).first()
            if next_step and assert_kw_id and str(next_step.keyword_id) == str(assert_kw_id):
                skipped_duplicates += 1
                continue
            insert_order = after_step.step_order + 1

            # 将该位置及之后的步骤序号 +1
            db.query(UIStep).filter(
                UIStep.case_id == case_id_uuid,
                UIStep.step_order >= insert_order
            ).update(
                {UIStep.step_order: UIStep.step_order + 1},
                synchronize_session=False
            )

            new_step = UIStep(
                keyword_id=keyword.id,
                step_name=f"{request.keyword_name}: {keyword.description}",
                parameters=request.parameters,
                enabled=True,
                continue_on_failure=request.continue_on_failure,
                screenshot_config={},
                case_id=case_id_uuid,
                scenario_id=case_item.scenario_id,
                task_id=scenario.task_id,
                step_order=insert_order,
                step_type=keyword.category
            )
            db.add(new_step)
            db.flush()
            created_steps.append(new_step)

            append_to_json_ids_field(case_item, 'step_ids', str(new_step.id))

        db.commit()

        # 刷新所有新建步骤
        for s in created_steps:
            db.refresh(s)

        invalidate_pattern("list_steps*")

        return {
            "message": f"已批量插入 {len(created_steps)} 个步骤" + (f"，跳过 {skipped_duplicates} 个重复" if skipped_duplicates > 0 else ""),
            "created_steps": [serialize_model(s) for s in created_steps],
            "inserted_count": len(created_steps),
            "skipped_duplicates": skipped_duplicates
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量插入步骤失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量插入步骤失败: {str(e)}")
