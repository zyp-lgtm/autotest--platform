"""
定时任务管理 API

提供定时任务的 CRUD 操作和管理功能
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..models.scheduled_job import ScheduledJob
from ..models.user import User
from ..models.ui_task import UITask
from ..core.database import get_db
from ..core.security import get_authenticated_user
from .utils import validate_and_fetch, validate_uuid, serialize_model
from ..services.scheduler import task_scheduler
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduled-jobs", tags=["定时任务管理"])


@router.post("/")
async def create_scheduled_job(
    job: dict,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """创建定时任务"""
    try:
        project_id = job.get("project_id")
        task_id = job.get("task_id")
        cron_expression = job.get("cron_expression")

        if not project_id or not task_id:
            raise HTTPException(status_code=400, detail="project_id 和 task_id 是必需的")

        # 转换为UUID对象
        try:
            from uuid import UUID
            project_id_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
            task_id_uuid = UUID(task_id) if isinstance(task_id, str) else task_id
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的UUID格式")

        # 验证项目存在
        from ..models.project import Project
        project = db.query(Project).filter(Project.id == project_id_uuid).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 验证任务存在
        task = db.query(UITask).filter(UITask.id == task_id_uuid).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 验证 cron 表达式
        if cron_expression:
            try:
                from apscheduler.triggers.cron import CronTrigger
                parts = cron_expression.split()
                if len(parts) != 5:
                    raise ValueError("Cron 表达式格式错误")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"无效的 cron 表达式: {str(e)}")

        # 创建定时任务
        new_job = ScheduledJob(
            project_id=project_id_uuid,
            name=job.get("name"),
            task_id=task_id_uuid,
            cron_expression=cron_expression,
            enabled=job.get("enabled", True),
            max_retries=job.get("max_retries", 3)
        )

        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        # 如果启用，添加到调度器
        if new_job.enabled:
            await task_scheduler.add_job(new_job)

        logger.info(f"用户 {user.username} 创建定时任务: {new_job.name}")
        return serialize_model(new_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建定时任务失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建定时任务失败: {str(e)}")


@router.get("/")
async def list_scheduled_jobs(
    project_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取定时任务列表"""
    query = db.query(ScheduledJob)

    if project_id:
        # 转换 project_id 为 UUID
        try:
            project_id_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
            query = query.filter(ScheduledJob.project_id == project_id_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的 project_id 格式")

    jobs = query.order_by(ScheduledJob.created_at.desc()).offset(skip).limit(limit).all()

    # 添加调度器状态信息
    result = []
    for job in jobs:
        job_data = serialize_model(job)
        job_status = task_scheduler.get_job_status(str(job.id))
        job_data["scheduler_status"] = job_status
        result.append(job_data)

    return result


@router.get("/{job_id}")
async def get_scheduled_job(
    job_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取定时任务详情"""
    job_uuid = validate_uuid(job_id, "定时任务")
    scheduled_job = validate_and_fetch(db, ScheduledJob, job_id, "定时任务")

    job_data = serialize_model(scheduled_job)
    job_status = task_scheduler.get_job_status(job_id)
    job_data["scheduler_status"] = job_status

    return job_data


@router.put("/{job_id}")
async def update_scheduled_job(
    job_id: str,
    job_update: dict,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """更新定时任务"""
    scheduled_job = validate_and_fetch(db, ScheduledJob, job_id, "定时任务")

    update_fields = ["name", "cron_expression", "enabled", "max_retries"]
    needs_scheduler_update = False

    for field in update_fields:
        if field in job_update:
            # 检查是否需要更新调度器
            if field in ["cron_expression", "enabled"]:
                needs_scheduler_update = True

            setattr(scheduled_job, field, job_update[field])

    db.commit()
    db.refresh(scheduled_job)

    # 更新调度器中的任务
    if needs_scheduler_update:
        if scheduled_job.enabled:
            await task_scheduler.add_job(scheduled_job)
        else:
            await task_scheduler.remove_job(job_id)

    logger.info(f"用户 {user.username} 更新定时任务: {scheduled_job.name}")
    return serialize_model(scheduled_job)


@router.delete("/{job_id}")
async def delete_scheduled_job(
    job_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """删除定时任务"""
    try:
        scheduled_job = validate_and_fetch(db, ScheduledJob, job_id, "定时任务")

        # 从调度器中移除
        await task_scheduler.remove_job(job_id)

        job_name = scheduled_job.name
        db.delete(scheduled_job)
        db.commit()

        logger.info(f"用户 {user.username} 删除定时任务: {job_name}")
        return {"message": "定时任务已删除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除定时任务失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除定时任务失败: {str(e)}")


@router.post("/{job_id}/pause")
async def pause_scheduled_job(
    job_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """暂停定时任务"""
    try:
        scheduled_job = validate_and_fetch(db, ScheduledJob, job_id, "定时任务")

        # 暂停调度器中的任务
        await task_scheduler.pause_job(job_id)

        logger.info(f"用户 {user.username} 暂停定时任务: {scheduled_job.name}")
        return {"message": "定时任务已暂停"}

    except Exception as e:
        logger.error(f"暂停定时任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"暂停定时任务失败: {str(e)}")


@router.post("/{job_id}/resume")
async def resume_scheduled_job(
    job_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """恢复定时任务"""
    try:
        scheduled_job = validate_and_fetch(db, ScheduledJob, job_id, "定时任务")

        # 恢复调度器中的任务
        await task_scheduler.resume_job(job_id)

        logger.info(f"用户 {user.username} 恢复定时任务: {scheduled_job.name}")
        return {"message": "定时任务已恢复"}

    except Exception as e:
        logger.error(f"恢复定时任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"恢复定时任务失败: {str(e)}")


@router.get("/stats/scheduler")
async def get_scheduler_stats(
    user: User = Depends(get_authenticated_user)
):
    """获取调度器统计信息"""
    try:
        stats = task_scheduler.get_stats()
        jobs_status = task_scheduler.get_all_jobs_status()

        return {
            "scheduler": stats,
            "jobs": jobs_status
        }

    except Exception as e:
        logger.error(f"获取调度器统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/trigger/{job_id}")
async def trigger_scheduled_job(
    job_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """手动触发定时任务"""
    try:
        scheduled_job = validate_and_fetch(db, ScheduledJob, job_id, "定时任务")

        # 在后台执行任务
        background_tasks = BackgroundTasks()
        background_tasks.add_task(task_scheduler._execute_scheduled_job, scheduled_job)

        logger.info(f"用户 {user.username} 手动触发定时任务: {scheduled_job.name}")
        return {"message": "定时任务已触发"}

    except Exception as e:
        logger.error(f"触发定时任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"触发定时任务失败: {str(e)}")
