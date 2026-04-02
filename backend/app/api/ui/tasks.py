from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...models.ui_task import UITask
from ...schemas.task import TaskCreate, TaskResponse

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


@router.post("/{task_id}/execute")
async def execute_ui_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    # TODO: 实现任务执行
    return {"execution_id": "exec_123", "status": "pending"}