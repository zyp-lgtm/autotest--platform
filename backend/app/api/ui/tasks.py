from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional, Dict, Any
import uuid

from ...models.ui_task import UITask, UIScenario, UICase, UIStep
from ...models.execution import TestExecution, ScenarioExecution, CaseExecution, StepExecution
from ...models.user import User
from ...schemas.task import TaskCreate, TaskUpdate, TaskResponse
from ...schemas.execution import ExecutionRequest
from ...core.database import get_db
from ...core.security import get_authenticated_user
from ...services.execution import TaskExecutor
from ...utils.cache import cache_response, invalidate_pattern
from ..utils import validate_and_fetch, validate_uuid, serialize_model
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ui/tasks", tags=["UI任务"])


@router.post("/")
@router.post("")
async def create_ui_task(
    task: TaskCreate,
    project_id: str = Query(..., description="项目ID"),
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """创建UI任务"""
    project_id_uuid = validate_uuid(project_id, "项目")

    new_task = UITask(**task.dict(), project_id=project_id_uuid)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # 清除任务列表缓存
    invalidate_pattern("list_ui_tasks*")

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
@router.get("")
@cache_response(ttl=300)  # 缓存 5 分钟
async def list_ui_tasks(
    project_id: str = Query(..., description="项目ID"),
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    project_id_uuid = validate_uuid(project_id, "项目")

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
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取任务详情"""
    task = validate_and_fetch(db, UITask, task_id, "任务")
    return serialize_model(task)


@router.post("/{task_id}/execute")
async def execute_ui_task(
    task_id: str,
    browser_config: Optional[Dict[str, Any]] = Body(None),
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """执行 UI 任务"""
    # 验证任务存在
    task = validate_and_fetch(db, UITask, task_id, "任务")

    # 验证并转换 task_id 为 UUID
    task_id_uuid = validate_uuid(task_id, "任务")

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
        user_id=user.id,
        execution_config=task.execution_config or {},
        browser_config=final_browser_config,
        environment="production"
    )

    # 创建执行器并执行
    executor = TaskExecutor(db)

    try:
        execution = await executor.execute_task(request)

        # 重新加载执行记录以获取完整的步骤日志（使用 eager loading 优化 N+1 查询）
        from ...models.execution import ScenarioExecution, CaseExecution, StepExecution

        # 使用 selectinload 预加载所有关联数据，将 61+ 次查询减少到 3 次
        execution = db.query(TestExecution).options(
            selectinload(TestExecution.scenario_executions).selectinload(ScenarioExecution.case_executions).selectinload(CaseExecution.step_executions)
        ).filter(TestExecution.id == execution.id).first()

        if not execution:
            raise HTTPException(status_code=404, detail="执行记录不存在")

        # 构建响应数据（所有数据已预加载，无需额外查询）
        scenarios_data = []
        for scenario_exec in execution.scenario_executions:
            cases_data = []
            for case_exec in scenario_exec.case_executions:
                steps_data = []
                for step_exec in case_exec.step_executions:
                    steps_data.append({
                        "step_name": step_exec.step_name,
                        "step_order": step_exec.step_order,
                        "keyword_name": step_exec.keyword_name,
                        "category": step_exec.category,
                        "status": step_exec.status,
                        "result": step_exec.result,
                        "duration": step_exec.duration,
                        "retry_attempt": step_exec.retry_attempt,
                        "continue_on_failure": step_exec.continue_on_failure,
                        "parameters": step_exec.parameters,
                        "error_message": step_exec.error_message,
                        "logs": step_exec.logs or [],
                        "screenshot_path": step_exec.screenshot_path,
                        "output": step_exec.output
                    })

                cases_data.append({
                    "id": str(case_exec.id),
                    "case_id": str(case_exec.case_id) if case_exec.case_id else None,
                    "status": case_exec.status,
                    "result": case_exec.result,
                    "total_steps": case_exec.total_steps,
                    "passed_steps": case_exec.passed_steps,
                    "failed_steps": case_exec.failed_steps,
                    "duration": case_exec.duration,
                    "error_message": case_exec.error_message,
                    "step_executions": steps_data
                })

            scenarios_data.append({
                "id": str(scenario_exec.id),
                "scenario_id": str(scenario_exec.scenario_id) if scenario_exec.scenario_id else None,
                "status": scenario_exec.status,
                "result": scenario_exec.result,
                "execution_order": scenario_exec.execution_order,
                "total_steps": scenario_exec.total_steps,
                "passed_steps": scenario_exec.passed_steps,
                "failed_steps": scenario_exec.failed_steps,
                "duration": scenario_exec.duration,
                "case_executions": cases_data
            })

        # 返回带日志的执行结果（使用完整的字段名 scenario_executions）
        return {
            "id": str(execution.id),
            "task_id": str(execution.task_id),
            "project_id": str(execution.project_id) if execution.project_id else None,
            "user_id": str(execution.user_id) if execution.user_id else None,
            "status": execution.status,
            "result": execution.result,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration": execution.duration,
            # 统计信息
            "total_scenarios": execution.total_scenarios,
            "total_cases": execution.total_cases,
            "total_steps": execution.total_steps,
            "passed_steps": execution.passed_steps,
            "failed_steps": execution.failed_steps,
            "skipped_steps": execution.skipped_steps or 0,
            "error_message": execution.error_message,
            "execution_mode": execution.execution_mode,
            # 使用完整的字段名，与前端期望保持一致
            "scenario_executions": scenarios_data
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
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """更新任务"""
    task = validate_and_fetch(db, UITask, task_id, "任务")

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
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """删除任务（级联删除关联的场景、用例、步骤和执行记录）"""
    import json

    # 验证并转换 UUID
    task_id_uuid = validate_uuid(task_id, "任务")
    task = validate_and_fetch(db, UITask, task_id, "任务")

    try:
        # 1. 删除执行记录（先删除子记录）
        from ...models.execution import (
            TestExecution, ScenarioExecution, CaseExecution, StepExecution
        )

        # 获取所有执行记录
        executions = db.query(TestExecution).filter(
            TestExecution.task_id == task_id_uuid
        ).all()

        for execution in executions:
            # 获取所有场景执行记录
            scenario_executions = db.query(ScenarioExecution).filter(
                ScenarioExecution.test_execution_id == execution.id
            ).all()

            for scenario_exec in scenario_executions:
                # 获取所有用例执行记录
                case_executions = db.query(CaseExecution).filter(
                    CaseExecution.scenario_execution_id == scenario_exec.id
                ).all()

                for case_exec in case_executions:
                    # 删除步骤执行记录
                    db.query(StepExecution).filter(
                        StepExecution.case_execution_id == case_exec.id
                    ).delete()
                    # 删除用例执行记录
                    db.delete(case_exec)

                # 删除场景执行记录
                db.delete(scenario_exec)

            # 删除执行记录
            db.delete(execution)

        # 2. 删除场景、用例、步骤
        scenarios = db.query(UIScenario).filter(
            UIScenario.task_id == task_id_uuid
        ).all()

        for scenario in scenarios:
            # 获取场景的所有用例
            cases = db.query(UICase).filter(
                UICase.scenario_id == scenario.id
            ).all()

            for case in cases:
                # 删除用例的所有步骤
                db.query(UIStep).filter(
                    UIStep.case_id == case.id
                ).delete()
                # 删除用例
                db.delete(case)

            # 删除场景
            db.delete(scenario)

        # 3. 删除任务
        db.delete(task)
        db.commit()

        # 4. 清除缓存
        try:
            from ...utils.cache import invalidate_pattern
            invalidate_pattern("list_tasks*")
        except Exception as e:
            logger.warning(f"清除缓存失败: {e}")

        return {"message": "任务已删除"}

    except Exception as e:
        db.rollback()
        logger.error(f"删除任务失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"删除任务失败: {str(e)}"
        )


@router.get("/{task_id}/executions")
async def get_task_executions(
    task_id: str,
    limit: int = Query(10, ge=1, le=100),
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取任务的执行记录"""
    task_id_uuid = validate_uuid(task_id, "任务")

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
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取单个执行记录详情"""
    # 使用 eager loading 优化 N+1 查询（将 61+ 次查询减少到 3 次）
    execution = db.query(TestExecution).options(
        selectinload(TestExecution.scenario_executions).selectinload(ScenarioExecution.case_executions).selectinload(CaseExecution.step_executions)
    ).filter(TestExecution.id == validate_uuid(execution_id, "执行")).first()

    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    # 构建响应数据（所有数据已预加载，无需额外查询）
    import json
    scenarios_data = []
    for scenario_exec in execution.scenario_executions:
        cases_data = []
        for case_exec in scenario_exec.case_executions:
            steps_data = []
            for step_exec in case_exec.step_executions:
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
