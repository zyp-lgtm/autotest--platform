"""
项目管理 API
提供项目的 CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..models.project import Project
from ..models.user import User
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from ..core.database import get_db
from ..core.security import get_authenticated_user
from ..utils.cache import cache_response, invalidate_pattern
from .utils import validate_and_fetch, validate_uuid, serialize_model
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["项目管理"])


@router.post("/")
@cache_response(ttl=60)  # 缓存 1 分钟
async def create_project(
    project: ProjectCreate,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """创建项目"""
    try:
        # 检查项目名称是否重复
        existing = db.query(Project).filter(Project.name == project.name).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"项目名称 '{project.name}' 已存在"
            )

        # 创建项目
        new_project = Project(
            name=project.name,
            description=project.description,
            owner_id=user.id
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        # 清除项目列表缓存
        try:
            invalidate_pattern("list_projects*")
        except Exception as e:
            logger.warning(f"清除缓存失败: {e}")

        logger.info(f"用户 {user.username} 创建项目: {new_project.name}")
        return serialize_model(new_project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建项目失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"创建项目失败: {str(e)}"
        )


@router.get("/")
@cache_response(ttl=300)  # 缓存 5 分钟
async def list_projects(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=100, description="返回记录数"),
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    projects = db.query(Project).order_by(Project.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for project in projects:
        result.append(serialize_model(project))

    return result


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取项目详情"""
    project = validate_and_fetch(db, Project, project_id, "项目")
    return serialize_model(project)


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """更新项目"""
    # 转换 project_id 为 UUID
    project_id_uuid = validate_uuid(project_id, "项目")
    project = validate_and_fetch(db, Project, project_id, "项目")

    # 检查权限（只有创建者可以修改）
    if project.owner_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="只有项目创建者可以修改项目"
        )

    update_data = project_update.dict(exclude_unset=True)

    # 如果修改名称，检查是否重复
    if "name" in update_data and update_data["name"] != project.name:
        existing = db.query(Project).filter(
            Project.name == update_data["name"],
            Project.id != project_id_uuid  # 使用 UUID 对象进行比较
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"项目名称 '{update_data['name']}' 已存在"
            )

    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    # 清除缓存
    try:
        invalidate_pattern("list_projects*")
        invalidate_pattern(f"get_project:{project_id}*")
    except Exception as e:
        logger.warning(f"清除缓存失败: {e}")

    logger.info(f"用户 {user.username} 更新项目: {project.name}")
    return serialize_model(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """删除项目"""
    try:
        project_id_uuid = validate_uuid(project_id, "项目")
        project = validate_and_fetch(db, Project, project_id, "项目")

        # 检查权限（只有创建者可以删除）
        if project.owner_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="只有项目创建者可以删除项目"
            )

        # 检查是否有关联的任务
        from ..models.ui_task import UITask
        task_count = db.query(UITask).filter(UITask.project_id == project_id_uuid).count()
        if task_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"项目下还有 {task_count} 个任务，无法删除。请先删除所有任务。"
            )

        project_name = project.name
        db.delete(project)
        db.commit()

        # 清除缓存
        try:
            invalidate_pattern("list_projects*")
            invalidate_pattern(f"get_project:{project_id}*")
        except Exception as e:
            logger.warning(f"清除缓存失败: {e}")

        logger.info(f"用户 {user.username} 删除项目: {project_name}")
        return {"message": "项目已删除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"删除项目失败: {str(e)}"
        )
