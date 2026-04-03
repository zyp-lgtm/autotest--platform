"""
场景管理 API
提供场景、用例、步骤的 CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from ...models.ui_task import UITask, UIScenario, UICase, UIStep
from ...models.keyword import Keyword
from ...schemas.scenario import ScenarioCreate, ScenarioUpdate, ScenarioResponse
from ...schemas.case import CaseCreate, CaseUpdate, CaseResponse
from ...schemas.step import StepCreate, StepUpdate, StepResponse
from ...core.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ui/scenarios", tags=["场景管理"])


# ==================== 场景管理 ====================

@router.post("/", response_model=ScenarioResponse)
async def create_scenario(
    scenario: ScenarioCreate,
    task_id: str,
    db: Session = Depends(get_db)
):
    """创建场景"""
    # 验证任务存在
    task = db.query(UITask).filter(UITask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 获取当前最大执行顺序
    max_order = db.query(UIScenario).filter(
        UIScenario.task_id == task_id
    ).count()

    new_scenario = UIScenario(
        **scenario.dict(),
        task_id=task_id,
        project_id=task.project_id,
        execution_order=max_order
    )
    db.add(new_scenario)
    db.commit()
    db.refresh(new_scenario)

    # 更新任务的场景列表
    if not task.scenario_ids:
        task.scenario_ids = []
    task.scenario_ids.append(new_scenario.id)
    db.commit()

    return new_scenario


@router.get("/", response_model=List[ScenarioResponse])
async def list_scenarios(
    task_id: str,
    db: Session = Depends(get_db)
):
    """获取任务的所有场景"""
    scenarios = db.query(UIScenario).filter(
        UIScenario.task_id == task_id
    ).order_by(UIScenario.execution_order).all()
    return scenarios


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """获取场景详情"""
    scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    return scenario


@router.put("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: str,
    scenario_update: ScenarioUpdate,
    db: Session = Depends(get_db)
):
    """更新场景"""
    scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    update_data = scenario_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scenario, field, value)

    db.commit()
    db.refresh(scenario)
    return scenario


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """删除场景"""
    scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    task_id = scenario.task_id

    # 删除场景及其关联的用例和步骤
    db.delete(scenario)
    db.commit()

    # 更新任务的场景列表
    task = db.query(UITask).filter(UITask.id == task_id).first()
    if task and task.scenario_ids:
        task.scenario_ids = [sid for sid in task.scenario_ids if sid != uuid.UUID(scenario_id)]
        db.commit()

    return {"message": "场景已删除"}


# ==================== 用例管理 ====================

@router.post("/{scenario_id}/cases", response_model=CaseResponse)
async def create_case(
    scenario_id: str,
    case: CaseCreate,
    db: Session = Depends(get_db)
):
    """创建用例"""
    scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    new_case = UICase(
        **case.dict(),
        scenario_id=scenario_id,
        project_id=scenario.project_id
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    # 更新场景的用例列表
    if not scenario.case_ids:
        scenario.case_ids = []
    scenario.case_ids.append(new_case.id)
    db.commit()

    return new_case


@router.get("/{scenario_id}/cases", response_model=List[CaseResponse])
async def list_cases(scenario_id: str, db: Session = Depends(get_db)):
    """获取场景的所有用例"""
    cases = db.query(UICase).filter(UICase.scenario_id == scenario_id).all()
    return cases


@router.put("/cases/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str,
    case_update: CaseUpdate,
    db: Session = Depends(get_db)
):
    """更新用例"""
    case = db.query(UICase).filter(UICase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    update_data = case_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)
    return case


@router.delete("/cases/{case_id}")
async def delete_case(case_id: str, db: Session = Depends(get_db)):
    """删除用例"""
    case = db.query(UICase).filter(UICase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    scenario_id = case.scenario_id

    db.delete(case)
    db.commit()

    # 更新场景的用例列表
    scenario = db.query(UIScenario).filter(UIScenario.id == scenario_id).first()
    if scenario and scenario.case_ids:
        scenario.case_ids = [cid for cid in scenario.case_ids if cid != uuid.UUID(case_id)]
        db.commit()

    return {"message": "用例已删除"}


# ==================== 步骤管理 ====================

@router.post("/cases/{case_id}/steps", response_model=StepResponse)
async def create_step(
    case_id: str,
    step: StepCreate,
    db: Session = Depends(get_db)
):
    """创建步骤"""
    case = db.query(UICase).filter(UICase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    # 验证关键字存在
    keyword = db.query(Keyword).filter(Keyword.id == step.keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键字不存在")

    # 获取当前最大步骤顺序
    max_order = db.query(UIStep).filter(UIStep.case_id == case_id).count()

    new_step = UIStep(
        **step.dict(),
        id=uuid.uuid4(),
        case_id=case_id,
        scenario_id=case.scenario_id,
        step_order=max_order,
        step_type=keyword.category
    )
    db.add(new_step)
    db.commit()
    db.refresh(new_step)

    # 更新用例的步骤列表
    if not case.step_ids:
        case.step_ids = []
    case.step_ids.append(new_step.id)
    db.commit()

    return new_step


@router.get("/cases/{case_id}/steps", response_model=List[StepResponse])
async def list_steps(case_id: str, db: Session = Depends(get_db)):
    """获取用例的所有步骤"""
    steps = db.query(UIStep).filter(UIStep.case_id == case_id).order_by(UIStep.step_order).all()
    return steps


@router.put("/steps/{step_id}", response_model=StepResponse)
async def update_step(
    step_id: str,
    step_update: StepUpdate,
    db: Session = Depends(get_db)
):
    """更新步骤"""
    step = db.query(UIStep).filter(UIStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    update_data = step_update.dict(exclude_unset=True)

    # 如果更新了关键字，更新步骤类型
    if 'keyword_id' in update_data:
        keyword = db.query(Keyword).filter(Keyword.id == update_data['keyword_id']).first()
        if keyword:
            update_data['step_type'] = keyword.category

    for field, value in update_data.items():
        setattr(step, field, value)

    db.commit()
    db.refresh(step)
    return step


@router.delete("/steps/{step_id}")
async def delete_step(step_id: str, db: Session = Depends(get_db)):
    """删除步骤"""
    step = db.query(UIStep).filter(UIStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    case_id = step.case_id

    db.delete(step)
    db.commit()

    # 更新用例的步骤列表
    case = db.query(UICase).filter(UICase.id == case_id).first()
    if case and case.step_ids:
        case.step_ids = [sid for sid in case.step_ids if sid != uuid.UUID(step_id)]
        db.commit()

    return {"message": "步骤已删除"}