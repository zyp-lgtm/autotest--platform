"""
场景管理 API
提供场景、用例、步骤的 CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from ...models.ui_task import UITask, UIScenario, UICase, UIStep
from ...models.keyword import Keyword
from ...schemas.scenario import ScenarioCreate, ScenarioUpdate, ScenarioResponse
from ...schemas.case import CaseCreate, CaseUpdate, CaseResponse
from ...schemas.step import StepCreate, StepUpdate, StepResponse
from ...core.database import get_db
from ...core.security import oauth2_scheme, verify_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ui/scenarios", tags=["场景管理"])


@router.post("/")
@router.post("")
async def create_scenario(
    scenario: ScenarioCreate,
    task_id: str = Query(..., description="任务ID"),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """创建场景"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        task_id_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的任务ID格式")

    # 验证任务存在
    task = db.query(UITask).filter(UITask.id == task_id_uuid).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 获取当前最大执行顺序
    max_order = db.query(UIScenario).filter(
        UIScenario.task_id == task_id_uuid
    ).count()

    new_scenario = UIScenario(
        **scenario.dict(),
        task_id=task_id_uuid,
        project_id=task.project_id,
        execution_order=max_order
    )
    db.add(new_scenario)
    db.commit()
    db.refresh(new_scenario)

    # 更新任务的场景列表（将 UUID 转换为字符串以支持 JSON 序列化）
    if not task.scenario_ids:
        task.scenario_ids = []
    task.scenario_ids.append(str(new_scenario.id))
    db.commit()

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


@router.get("/")
@router.get("")
async def list_scenarios(
    task_id: str = Query(..., description="任务ID"),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取任务的所有场景"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        task_id_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的任务ID格式")

    scenarios = db.query(UIScenario).filter(
        UIScenario.task_id == task_id_uuid
    ).order_by(UIScenario.execution_order).all()

    # 简化序列化
    result = []
    for scenario in scenarios:
        result.append({
            "id": str(scenario.id),
            "task_id": str(scenario.task_id),
            "project_id": str(scenario.project_id),
            "name": scenario.name,
            "description": scenario.description,
            "scenario_type": scenario.scenario_type,
            "execution_order": scenario.execution_order,
            "case_ids": [str(cid) for cid in (scenario.case_ids or [])],
            "tags": list(scenario.tags) if scenario.tags else [],
            "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
            "updated_at": scenario.updated_at.isoformat() if scenario.updated_at else None
        })
    return result


@router.get("/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取场景详情"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        scenario_id_uuid = uuid.UUID(scenario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的场景ID格式")

    scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id_uuid).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    # 手动序列化
    return {
        "id": str(scenario.id),
        "task_id": str(scenario.task_id),
        "project_id": str(scenario.project_id),
        "name": scenario.name,
        "description": scenario.description,
        "scenario_type": scenario.scenario_type,
        "execution_order": scenario.execution_order,
        "case_ids": [str(cid) for cid in (scenario.case_ids or [])],
        "tags": list(scenario.tags) if scenario.tags else [],
        "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
        "updated_at": scenario.updated_at.isoformat() if scenario.updated_at else None
    }


@router.put("/{scenario_id}")
async def update_scenario(
    scenario_id: str,
    scenario_update: ScenarioUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新场景"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        scenario_id_uuid = uuid.UUID(scenario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的场景ID格式")

    scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id_uuid).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    update_data = scenario_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scenario, field, value)

    db.commit()
    db.refresh(scenario)

    # 手动序列化
    return {
        "id": str(scenario.id),
        "task_id": str(scenario.task_id),
        "project_id": str(scenario.project_id),
        "name": scenario.name,
        "description": scenario.description,
        "scenario_type": scenario.scenario_type,
        "execution_order": scenario.execution_order,
        "case_ids": [str(cid) for cid in (scenario.case_ids or [])],
        "tags": list(scenario.tags) if scenario.tags else [],
        "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
        "updated_at": scenario.updated_at.isoformat() if scenario.updated_at else None
    }


@router.delete("/{scenario_id}")
async def delete_scenario(
    scenario_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """删除场景"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        scenario_id_uuid = uuid.UUID(scenario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的场景ID格式")

    scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id_uuid).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    task_id = scenario.task_id

    # 删除场景及其关联的用例和步骤
    db.delete(scenario)
    db.commit()

    # 更新任务的场景列表（将 UUID 转换为字符串以支持 JSON 序列化）
    task = db.query(UITask).filter(UITask.id == task_id).first()
    if task and task.scenario_ids:
        task.scenario_ids = [sid for sid in task.scenario_ids if sid != str(scenario_id_uuid)]
        db.commit()

    return {"message": "场景已删除"}


# ==================== 用例管理 ====================

@router.post("/{scenario_id}/cases")
async def create_case(
    scenario_id: str,
    case: CaseCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """创建用例"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        scenario_id_uuid = uuid.UUID(scenario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的场景ID格式")

    scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id_uuid).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    new_case = UICase(
        **case.dict(),
        scenario_id=scenario_id_uuid,
        project_id=scenario.project_id
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)

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
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取场景的所有用例"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        scenario_id_uuid = uuid.UUID(scenario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的场景ID格式")

    cases = db.query(UICase).filter(UICase.scenario_id == scenario_id_uuid).all()

    # 简化序列化
    result = []
    for case_item in cases:
        result.append({
            "id": str(case_item.id),
            "scenario_id": str(case_item.scenario_id),
            "project_id": str(case_item.project_id),
            "name": case_item.name,
            "description": case_item.description,
            "case_type": case_item.case_type,
            "step_ids": [str(sid) for sid in (case_item.step_ids or [])],
            "priority": case_item.priority,
            "tags": list(case_item.tags) if case_item.tags else [],
            "data_bindings": case_item.data_bindings or {},
            "browser_config": case_item.browser_config or {},
            "created_at": case_item.created_at.isoformat() if case_item.created_at else None,
            "updated_at": case_item.updated_at.isoformat() if case_item.updated_at else None
        })
    return result


@router.put("/cases/{case_id}")
async def update_case(
    case_id: str,
    case_update: CaseUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新用例"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        case_id_uuid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用例ID格式")

    case_item = db.query(UICase).filter(UICase.id == case_id_uuid).first()
    if not case_item:
        raise HTTPException(status_code=404, detail="用例不存在")

    update_data = case_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case_item, field, value)

    db.commit()
    db.refresh(case_item)

    # 手动序列化
    return {
        "id": str(case_item.id),
        "scenario_id": str(case_item.scenario_id),
        "project_id": str(case_item.project_id),
        "name": case_item.name,
        "description": case_item.description,
        "case_type": case_item.case_type,
        "step_ids": [str(sid) for sid in (case_item.step_ids or [])],
        "priority": case_item.priority,
        "tags": list(case_item.tags) if case_item.tags else [],
        "data_bindings": case_item.data_bindings or {},
        "browser_config": case_item.browser_config or {},
        "created_at": case_item.created_at.isoformat() if case_item.created_at else None,
        "updated_at": case_item.updated_at.isoformat() if case_item.updated_at else None
    }


@router.delete("/cases/{case_id}")
async def delete_case(
    case_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """删除用例"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        case_id_uuid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用例ID格式")

    case_item = db.query(UICase).filter(UICase.id == case_id_uuid).first()
    if not case_item:
        raise HTTPException(status_code=404, detail="用例不存在")

    scenario_id = case_item.scenario_id

    db.delete(case_item)
    db.commit()

    # 更新场景的用例列表（将 UUID 转换为字符串以支持 JSON 序列化）
    scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id).first()
    if scenario and scenario.case_ids:
        scenario.case_ids = [cid for cid in scenario.case_ids if cid != str(case_id_uuid)]
        db.commit()

    return {"message": "用例已删除"}


# ==================== 步骤管理 ====================

@router.post("/cases/{case_id}/steps")
async def create_step(
    case_id: str,
    step: StepCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """创建步骤"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        case_id_uuid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用例ID格式")

    case_item = db.query(UICase).filter(UICase.id == case_id_uuid).first()
    if not case_item:
        raise HTTPException(status_code=404, detail="用例不存在")

    # 获取场景和任务信息
    scenario = db.query(UIScenario).filter(UIScenario.id == case_item.scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    # 验证关键字存在
    keyword = db.query(Keyword).filter(Keyword.id == step.keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键字不存在")

    # 获取当前最大步骤顺序
    max_order = db.query(UIStep).filter(UIStep.case_id == case_id_uuid).count()

    new_step = UIStep(
        **step.dict(),
        id=uuid.uuid4(),
        case_id=case_id_uuid,
        scenario_id=case_item.scenario_id,
        task_id=scenario.task_id,
        step_order=max_order,
        step_type=keyword.category
    )
    db.add(new_step)
    db.commit()
    db.refresh(new_step)

    # 更新用例的步骤列表（将 UUID 转换为字符串以支持 JSON 序列化）
    if not case_item.step_ids:
        case_item.step_ids = []
    case_item.step_ids.append(str(new_step.id))
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


@router.get("/cases/{case_id}/steps")
async def list_steps(
    case_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取用例的所有步骤"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        case_id_uuid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用例ID格式")

    steps = db.query(UIStep).filter(UIStep.case_id == case_id_uuid).order_by(UIStep.step_order).all()

    # 简化序列化
    result = []
    for step_item in steps:
        result.append({
            "id": str(step_item.id),
            "case_id": str(step_item.case_id),
            "scenario_id": str(step_item.scenario_id),
            "task_id": str(step_item.task_id),
            "step_order": step_item.step_order,
            "keyword_id": str(step_item.keyword_id),
            "step_name": step_item.step_name,
            "step_type": step_item.step_type,
            "parameters": step_item.parameters or {},
            "enabled": step_item.enabled,
            "continue_on_failure": step_item.continue_on_failure,
            "screenshot_config": step_item.screenshot_config or {},
            "created_at": step_item.created_at.isoformat() if step_item.created_at else None,
            "updated_at": step_item.updated_at.isoformat() if step_item.updated_at else None
        })
    return result


@router.put("/steps/{step_id}")
async def update_step(
    step_id: str,
    step_update: StepUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新步骤"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        step_id_uuid = uuid.UUID(step_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的步骤ID格式")

    step_item = db.query(UIStep).filter(UIStep.id == step_id_uuid).first()
    if not step_item:
        raise HTTPException(status_code=404, detail="步骤不存在")

    update_data = step_update.dict(exclude_unset=True)

    # 如果更新了关键字，更新步骤类型
    if 'keyword_id' in update_data:
        keyword = db.query(Keyword).filter(Keyword.id == update_data['keyword_id']).first()
        if keyword:
            update_data['step_type'] = keyword.category

    for field, value in update_data.items():
        setattr(step_item, field, value)

    db.commit()
    db.refresh(step_item)

    # 手动序列化
    return {
        "id": str(step_item.id),
        "case_id": str(step_item.case_id),
        "scenario_id": str(step_item.scenario_id),
        "task_id": str(step_item.task_id),
        "step_order": step_item.step_order,
        "keyword_id": str(step_item.keyword_id),
        "step_name": step_item.step_name,
        "step_type": step_item.step_type,
        "parameters": step_item.parameters or {},
        "enabled": step_item.enabled,
        "continue_on_failure": step_item.continue_on_failure,
        "screenshot_config": step_item.screenshot_config or {},
        "created_at": step_item.created_at.isoformat() if step_item.created_at else None,
        "updated_at": step_item.updated_at.isoformat() if step_item.updated_at else None
    }


@router.delete("/steps/{step_id}")
async def delete_step(
    step_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """删除步骤"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        step_id_uuid = uuid.UUID(step_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的步骤ID格式")

    step_item = db.query(UIStep).filter(UIStep.id == step_id_uuid).first()
    if not step_item:
        raise HTTPException(status_code=404, detail="步骤不存在")

    case_id = step_item.case_id

    db.delete(step_item)
    db.commit()

    # 更新用例的步骤列表（将 UUID 转换为字符串以支持 JSON 序列化）
    case_item = db.query(UICase).filter(UICase.id == case_id).first()
    if case_item and case_item.step_ids:
        case_item.step_ids = [sid for sid in case_item.step_ids if sid != str(step_id_uuid)]
        db.commit()

    return {"message": "步骤已删除"}
