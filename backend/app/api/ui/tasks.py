from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid

from ...models.ui_task import UITask
from ...models.execution import TestExecution, ScenarioExecution, CaseExecution, StepExecution
from ...schemas.task import TaskCreate, TaskUpdate, TaskResponse
from ...schemas.execution import ExecutionRequest
from ...core.database import get_db
from ...core.security import oauth2_scheme, verify_token
from ...services.executor import TaskExecutor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ui/tasks", tags=["UI任务"])


@router.post("/")
async def create_ui_task(
    task: TaskCreate,
    project_id: str = Query(..., description="项目ID"),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """创建UI任务"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        project_id_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的项目ID格式")

    new_task = UITask(**task.dict(), project_id=project_id_uuid)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {
        "id": str(new_task.id),
        "project_id": str(new_task.project_id),
        "name": new_task.name,
        "description": new_task.description,
        "task_type": new_task.task_type,
        "scenario_ids": [str(sid) for sid in (new_task.scenario_ids or [])],
        "tags": list(new_task.tags) if new_task.tags else [],
        "created_at": new_task.created_at.isoformat() if new_task.created_at else None
    }


@router.get("/")
async def list_ui_tasks(
    project_id: str = Query(..., description="项目ID"),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        project_id_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的项目ID格式")

    tasks = db.query(UITask).filter(
        UITask.project_id == project_id_uuid
    ).order_by(UITask.created_at.desc()).all()

    result = []
    for task in tasks:
        result.append({
            "id": str(task.id),
            "project_id": str(task.project_id),
            "name": task.name,
            "description": task.description,
            "task_type": task.task_type,
            "scenario_ids": [str(sid) for sid in (task.scenario_ids or [])],
            "tags": list(task.tags) if task.tags else [],
            "created_at": task.created_at.isoformat() if task.created_at else None
        })
    return result


@router.get("/{task_id}")
async def get_ui_task(
    task_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取任务详情"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        task_id_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的任务ID格式")

    task = db.query(UITask).filter(UITask.id == task_id_uuid).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "id": str(task.id),
        "project_id": str(task.project_id),
        "name": task.name,
        "description": task.description,
        "task_type": task.task_type,
        "scenario_ids": [str(sid) for sid in (task.scenario_ids or [])],
        "tags": list(task.tags) if task.tags else [],
        "created_at": task.created_at.isoformat() if task.created_at else None
    }


@router.post("/{task_id}/execute")
async def execute_ui_task(
    task_id: str,
    browser_config: Optional[Dict[str, Any]] = Body(None),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """执行 UI 任务"""
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

    # 合并浏览器配置（优先级：API参数 > 任务配置 > 默认值）
    final_browser_config = {"headless": False}  # 默认显示浏览器

    # 1. 先应用任务的默认配置
    if task.execution_config and "browser_config" in task.execution_config:
        final_browser_config.update(task.execution_config["browser_config"])

    # 2. 再用 API 参数覆盖（如果提供）
    if browser_config:
        # 如果 browser_config 中嵌套了 browser_config 键，提取内部配置
        if "browser_config" in browser_config:
            final_browser_config.update(browser_config["browser_config"])
        else:
            final_browser_config.update(browser_config)

    # 创建执行请求
    request = ExecutionRequest(
        task_id=task_id_uuid,
        execution_config=task.execution_config or {},
        browser_config=final_browser_config,
        environment="production"
    )

    # 创建执行器并执行
    executor = TaskExecutor(db)

    try:
        execution = await executor.execute_task(request)

        # 重新加载执行记录以获取完整的步骤日志
        db.refresh(execution)

        # 加载步骤执行详情
        from ...models.execution import ScenarioExecution, CaseExecution, StepExecution

        scenario_executions = db.query(ScenarioExecution).filter(
            ScenarioExecution.test_execution_id == execution.id
        ).all()

        scenarios_data = []
        for scenario_exec in scenario_executions:
            case_executions = db.query(CaseExecution).filter(
                CaseExecution.scenario_execution_id == scenario_exec.id
            ).all()

            cases_data = []
            for case_exec in case_executions:
                step_executions = db.query(StepExecution).filter(
                    StepExecution.case_execution_id == case_exec.id
                ).order_by(StepExecution.step_order).all()

                steps_data = []
                for step_exec in step_executions:
                    steps_data.append({
                        "step_name": step_exec.step_name,
                        "step_order": step_exec.step_order,
                        "keyword_name": step_exec.keyword_name,
                        "status": step_exec.status,
                        "result": step_exec.result,
                        "duration": step_exec.duration,
                        "error_message": step_exec.error_message,
                        "logs": step_exec.logs or [],
                        "screenshot_path": step_exec.screenshot_path
                    })

                cases_data.append({
                    "status": case_exec.status,
                    "result": case_exec.result,
                    "total_steps": case_exec.total_steps,
                    "passed_steps": case_exec.passed_steps,
                    "failed_steps": case_exec.failed_steps,
                    "steps": steps_data
                })

            scenarios_data.append({
                "status": scenario_exec.status,
                "result": scenario_exec.result,
                "cases": cases_data
            })

        # 返回带日志的执行结果
        return {
            "id": str(execution.id),
            "task_id": str(execution.task_id),
            "status": execution.status,
            "result": execution.result,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration": execution.duration,
            "total_steps": execution.total_steps,
            "passed_steps": execution.passed_steps,
            "failed_steps": execution.failed_steps,
            "error_message": execution.error_message,
            "execution_mode": execution.execution_mode,
            "scenarios": scenarios_data
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Task execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.put("/{task_id}")
async def update_ui_task(
    task_id: str,
    task_update: TaskUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新任务"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        task_id_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的任务ID格式")

    task = db.query(UITask).filter(UITask.id == task_id_uuid).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 更新非空字段
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return {
        "id": str(task.id),
        "project_id": str(task.project_id),
        "name": task.name,
        "description": task.description,
        "task_type": task.task_type,
        "scenario_ids": [str(sid) for sid in (task.scenario_ids or [])],
        "tags": list(task.tags) if task.tags else [],
        "created_at": task.created_at.isoformat() if task.created_at else None
    }


@router.delete("/{task_id}")
async def delete_ui_task(
    task_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """删除任务"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        task_id_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的任务ID格式")

    task = db.query(UITask).filter(UITask.id == task_id_uuid).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    db.delete(task)
    db.commit()
    return {"message": "任务已删除"}


@router.get("/{task_id}/executions")
async def get_task_executions(
    task_id: str,
    limit: int = Query(10, ge=1, le=100),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取任务的执行记录"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        task_id_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的任务ID格式")

    executions = db.query(TestExecution).filter(
        TestExecution.task_id == task_id_uuid
    ).order_by(TestExecution.created_at.desc()).limit(limit).all()

    # 简化序列化，只返回基本信息
    result = []
    for execution in executions:
        result.append({
            "id": str(execution.id),
            "task_id": str(execution.task_id),
            "status": execution.status,
            "result": execution.result,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration": execution.duration,
            "total_scenarios": execution.total_scenarios,
            "total_cases": execution.total_cases,
            "total_steps": execution.total_steps,
            "passed_steps": execution.passed_steps,
            "failed_steps": execution.failed_steps,
            "skipped_steps": execution.skipped_steps,
            "error_message": execution.error_message
        })
    return result


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取单个执行记录详情"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        execution_id_uuid = uuid.UUID(execution_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的执行ID格式")

    execution = db.query(TestExecution).filter(
        TestExecution.id == execution_id_uuid
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    # 加载关联数据
    scenario_executions = db.query(ScenarioExecution).filter(
        ScenarioExecution.test_execution_id == execution.id
    ).order_by(ScenarioExecution.execution_order).all()

    scenarios_data = []
    for scenario_exec in scenario_executions:
        # 加载用例
        case_executions = db.query(CaseExecution).filter(
            CaseExecution.scenario_execution_id == scenario_exec.id
        ).all()

        cases_data = []
        for case_exec in case_executions:
            # 加载步骤
            step_executions = db.query(StepExecution).filter(
                StepExecution.case_execution_id == case_exec.id
            ).order_by(StepExecution.step_order).all()

            steps_data = []
            for step_exec in step_executions:
                # 解析 debug_info JSON 字符串
                debug_info = None
                if step_exec.debug_info:
                    import json
                    try:
                        debug_info = json.loads(step_exec.debug_info) if isinstance(step_exec.debug_info, str) else step_exec.debug_info
                    except:
                        debug_info = step_exec.debug_info

                steps_data.append({
                    "id": str(step_exec.id),
                    "step_id": str(step_exec.step_id),
                    "step_name": step_exec.step_name,
                    "step_order": step_exec.step_order,
                    "keyword_name": step_exec.keyword_name,
                    "category": step_exec.category,
                    "status": step_exec.status,
                    "result": step_exec.result,
                    "duration": step_exec.duration,
                    "error_message": step_exec.error_message,
                    "screenshot_path": step_exec.screenshot_path,
                    "continue_on_failure": step_exec.continue_on_failure,
                    "logs": step_exec.logs or [],
                    "output": step_exec.output,
                    "debug_info": debug_info,
                    "created_at": step_exec.created_at.isoformat() if step_exec.created_at else None
                })

            cases_data.append({
                "id": str(case_exec.id),
                "status": case_exec.status,
                "result": case_exec.result,
                "total_steps": case_exec.total_steps,
                "passed_steps": case_exec.passed_steps,
                "failed_steps": case_exec.failed_steps,
                "error_message": case_exec.error_message,
                "step_executions": steps_data
            })

        scenarios_data.append({
            "id": str(scenario_exec.id),
            "status": scenario_exec.status,
            "result": scenario_exec.result,
            "execution_order": scenario_exec.execution_order,
            "total_cases": scenario_exec.total_cases,
            "total_steps": scenario_exec.total_steps,
            "passed_steps": scenario_exec.passed_steps,
            "failed_steps": scenario_exec.failed_steps,
            "case_executions": cases_data
        })

    return {
        "id": str(execution.id),
        "task_id": str(execution.task_id),
        "status": execution.status,
        "result": execution.result,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "duration": execution.duration,
        "total_scenarios": execution.total_scenarios,
        "total_cases": execution.total_cases,
        "total_steps": execution.total_steps,
        "passed_steps": execution.passed_steps,
        "failed_steps": execution.failed_steps,
        "skipped_steps": execution.skipped_steps,
        "error_message": execution.error_message,
        "execution_mode": execution.execution_mode,
        "scenario_executions": scenarios_data
    }
