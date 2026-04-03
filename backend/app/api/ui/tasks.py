from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid
from ...models.ui_task import UITask
from ...schemas.task import TaskCreate, TaskUpdate, TaskResponse
from ...schemas.execution import ExecutionRequest, TestExecutionResponse
from ...core.database import get_db
from ...services.executor import TaskExecutor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ui/tasks", tags=["UI任务"])


@router.post("/", response_model=TaskResponse)
async def create_ui_task(
    task: TaskCreate,
    project_id: str,
    db: Session = Depends(get_db)
):
    new_task = UITask(**task.dict(), project_id=project_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.get("/", response_model=List[TaskResponse])
async def list_ui_tasks(project_id: str, db: Session = Depends(get_db)):
    tasks = db.query(UITask).filter(UITask.project_id == project_id).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_ui_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(UITask).filter(UITask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.post("/{task_id}/execute", response_model=TestExecutionResponse)
async def execute_ui_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """执行 UI 任务"""
    # 验证任务存在
    task = db.query(UITask).filter(UITask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 创建执行请求
    request = ExecutionRequest(
        task_id=uuid.UUID(task_id),
        execution_config=task.execution_config or {},
        browser_config={"headless": True},  # 默认无头模式
        environment="production"
    )

    # 创建执行器并执行
    executor = TaskExecutor(db)

    try:
        execution = await executor.execute_task(request)
        return execution
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Task execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_ui_task(
    task_id: str,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    task = db.query(UITask).filter(UITask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 更新非空字段
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
async def delete_ui_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    task = db.query(UITask).filter(UITask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    db.delete(task)
    db.commit()
    return {"message": "任务已删除"}