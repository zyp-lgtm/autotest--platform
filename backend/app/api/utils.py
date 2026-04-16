"""
API 工具函数

提供通用的 API 处理函数，减少代码重复
"""
from typing import Type, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta
from fastapi import HTTPException
import uuid
import logging

logger = logging.getLogger(__name__)

# TypeVar for SQLAlchemy models
T = TypeVar('T', bound=DeclarativeMeta)


def validate_and_fetch(
    db: Session,
    model: Type[T],
    entity_id: str,
    entity_name: str
) -> T:
    """
    验证 UUID 并获取实体

    通用的工具函数，用于替代重复的 UUID 验证和查询逻辑

    Args:
        db: 数据库会话
        model: SQLAlchemy 模型类
        entity_id: 实体 ID 字符串
        entity_name: 实体名称（用于错误消息）

    Returns:
        查询到的实体对象

    Raises:
        HTTPException 400: UUID 格式无效
        HTTPException 404: 实体不存在

    Example:
        >>> task = validate_and_fetch(db, UITask, task_id, "任务")
        >>> scenario = validate_and_fetch(db, UIScenario, scenario_id, "场景")
    """
    # 验证 UUID 格式
    try:
        eid = uuid.UUID(entity_id)
    except ValueError as e:
        logger.warning(f"无效的{entity_name}ID格式: {entity_id}")
        raise HTTPException(
            status_code=400,
            detail=f"无效的{entity_name}ID格式"
        )

    # 查询实体
    entity = db.query(model).filter(model.id == eid).first()
    if not entity:
        logger.info(f"{entity_name}不存在: {entity_id}")
        raise HTTPException(
            status_code=404,
            detail=f"{entity_name}不存在"
        )

    return entity


def validate_uuid(
    entity_id: str,
    entity_name: str = "实体"
) -> uuid.UUID:
    """
    验证 UUID 格式

    Args:
        entity_id: UUID 字符串
        entity_name: 实体名称（用于错误消息）

    Returns:
        验证后的 UUID 对象

    Raises:
        HTTPException 400: UUID 格式无效

    Example:
        >>> task_id = validate_uuid(task_id_str, "任务")
    """
    try:
        return uuid.UUID(entity_id)
    except ValueError:
        logger.warning(f"无效的{entity_name}ID格式: {entity_id}")
        raise HTTPException(
            status_code=400,
            detail=f"无效的{entity_name}ID格式"
        )


def serialize_model(
    model_obj,
    include_fields: list = None,
    exclude_fields: list = None
) -> dict:
    """
    通用模型序列化函数

    Args:
        model_obj: SQLAlchemy 模型实例
        include_fields: 包含的字段列表
        exclude_fields: 排除的字段列表

    Returns:
        序列化后的字典

    Example:
        >>> result = serialize_model(task, include_fields=['id', 'name'])
    """
    if model_obj is None:
        return None

    # 获取所有列
    result = {}
    for column in model_obj.__table__.columns:
        col_name = column.name

        # 字段过滤
        if include_fields and col_name not in include_fields:
            continue
        if exclude_fields and col_name in exclude_fields:
            continue

        value = getattr(model_obj, col_name)

        # UUID 转字符串
        if isinstance(value, uuid.UUID):
            value = str(value)
        # datetime 转 ISO 格式
        elif hasattr(value, 'isoformat'):
            value = value.isoformat() if value else None
        # JSON 类型处理
        elif col_name.endswith('_ids') and isinstance(value, list):
            value = [str(v) for v in value]
        elif col_name.endswith('_ids') and isinstance(value, str):
            # 已经是字符串的 JSON 数组
            import json
            try:
                value = json.loads(value)
            except:
                value = []

        result[col_name] = value

    return result
