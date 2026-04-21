"""
环境配置管理 API

提供环境配置的 CRUD 操作和管理功能
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..models.environment import Environment
from ..models.user import User
from ..models.project import Project
from ..core.database import get_db
from ..core.security import get_authenticated_user
from .utils import validate_and_fetch, validate_uuid, serialize_model
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/environments", tags=["环境配置管理"])


@router.post("/")
async def create_environment(
    environment: dict,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """创建环境配置"""
    try:
        project_id = environment.get("project_id")
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id 是必需的")

        # 转换为UUID对象
        try:
            project_id_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的 project_id 格式")

        # 验证项目存在
        project = db.query(Project).filter(Project.id == project_id_uuid).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 检查是否设置为默认环境
        is_default = environment.get("is_default", False)

        # 如果设置为默认环境，取消其他环境的默认状态
        if is_default:
            db.query(Environment).filter(
                Environment.project_id == project_id_uuid,
                Environment.is_default == True
            ).update({"is_default": False})

        # 创建环境配置
        new_environment = Environment(
            project_id=project_id_uuid,
            name=environment.get("name"),
            base_url=environment.get("base_url"),
            variables=environment.get("variables", {}),
            is_default=is_default
        )

        db.add(new_environment)
        db.commit()
        db.refresh(new_environment)

        logger.info(f"用户 {user.username} 创建环境配置: {new_environment.name}")
        return serialize_model(new_environment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建环境配置失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建环境配置失败: {str(e)}")


@router.get("/")
async def list_environments(
    project_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取环境配置列表"""
    query = db.query(Environment)

    if project_id:
        # 转换 project_id 为 UUID
        try:
            project_id_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
            query = query.filter(Environment.project_id == project_id_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的 project_id 格式")

    environments = query.order_by(Environment.created_at.desc()).offset(skip).limit(limit).all()

    return [serialize_model(env) for env in environments]


@router.get("/{environment_id}")
async def get_environment(
    environment_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取环境配置详情"""
    env_uuid = validate_uuid(environment_id, "环境配置")
    environment = validate_and_fetch(db, Environment, environment_id, "环境配置")
    return serialize_model(environment)


@router.get("/project/{project_id}/default")
async def get_default_environment(
    project_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取项目的默认环境配置"""
    environment = db.query(Environment).filter(
        Environment.project_id == project_id,
        Environment.is_default == True
    ).first()

    if not environment:
        # 如果没有默认环境，返回第一个环境
        environment = db.query(Environment).filter(
            Environment.project_id == project_id
        ).first()

    if environment:
        return serialize_model(environment)
    else:
        return {"message": "项目没有配置环境"}


@router.put("/{environment_id}")
async def update_environment(
    environment_id: str,
    environment_update: dict,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """更新环境配置"""
    environment = validate_and_fetch(db, Environment, environment_id, "环境配置")

    update_fields = ["name", "base_url", "variables", "is_default"]
    for field in update_fields:
        if field in environment_update:
            # 如果设置为默认环境，取消其他环境的默认状态
            if field == "is_default" and environment_update[field]:
                db.query(Environment).filter(
                    Environment.project_id == environment.project_id,
                    Environment.id != environment.id,
                    Environment.is_default == True
                ).update({"is_default": False})

            setattr(environment, field, environment_update[field])

    db.commit()
    db.refresh(environment)

    logger.info(f"用户 {user.username} 更新环境配置: {environment.name}")
    return serialize_model(environment)


@router.delete("/{environment_id}")
async def delete_environment(
    environment_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """删除环境配置"""
    try:
        environment = validate_and_fetch(db, Environment, environment_id, "环境配置")

        # 不允许删除默认环境
        if environment.is_default:
            raise HTTPException(
                status_code=400,
                detail="不能删除默认环境，请先设置其他环境为默认"
            )

        env_name = environment.name
        db.delete(environment)
        db.commit()

        logger.info(f"用户 {user.username} 删除环境配置: {env_name}")
        return {"message": "环境配置已删除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除环境配置失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除环境配置失败: {str(e)}")


@router.post("/{environment_id}/set-default")
async def set_default_environment(
    environment_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """设置默认环境"""
    try:
        environment = validate_and_fetch(db, Environment, environment_id, "环境配置")

        # 取消其他环境的默认状态
        db.query(Environment).filter(
            Environment.project_id == environment.project_id,
            Environment.id != environment.id,
            Environment.is_default == True
        ).update({"is_default": False})

        # 设置当前环境为默认
        environment.is_default = True
        db.commit()
        db.refresh(environment)

        logger.info(f"用户 {user.username} 设置默认环境: {environment.name}")
        return serialize_model(environment)

    except Exception as e:
        logger.error(f"设置默认环境失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"设置默认环境失败: {str(e)}")
