"""
仪表盘统计 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.ui_task import UITask
from ..models.ui_task import UIScenario, UICase, UIStep
from ..models.execution import TestExecution
from ..models.user import User
from ..core.database import get_db
from ..core.security import get_authenticated_user

router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("/dashboard")
async def get_dashboard_stats(
    project_id: str = Query(..., description="项目ID"),
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取仪表盘统计信息（单次查询聚合）"""
    from ..api.utils import validate_uuid
    pid = validate_uuid(project_id, "项目")

    total_tasks = db.query(func.count(UITask.id)).filter(
        UITask.project_id == pid
    ).scalar() or 0

    total_scenarios = db.query(func.count(UIScenario.id)).filter(
        UIScenario.project_id == pid
    ).scalar() or 0

    total_cases = db.query(func.count(UICase.id)).filter(
        UICase.project_id == pid
    ).scalar() or 0

    total_steps = db.query(func.count(UIStep.id)).join(
        UIScenario, UIStep.scenario_id == UIScenario.id
    ).filter(
        UIScenario.project_id == pid
    ).scalar() or 0

    recent_executions = db.query(func.count(TestExecution.id)).filter(
        TestExecution.project_id == pid
    ).scalar() or 0

    return {
        "total_tasks": total_tasks,
        "total_scenarios": total_scenarios,
        "total_cases": total_cases,
        "total_steps": total_steps,
        "recent_executions": recent_executions,
    }
