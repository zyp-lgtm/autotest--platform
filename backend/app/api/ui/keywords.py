"""
关键字 API
提供关键字查询、创建、更新、删除接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging

from ...models.keyword import Keyword
from ...models.user import User
from ...core.database import get_db
from ...core.security import get_authenticated_user
from ...schemas.keyword import KeywordCreate, KeywordResponse
from ...utils.cache import cache_response, invalidate_pattern
from ..utils import validate_and_fetch

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ui/keywords", tags=["UI关键字"])


@router.get("/")
@router.get("")
@cache_response(ttl=300)  # 缓存 5 分钟
async def list_keywords(
    category: Optional[str] = Query(None, description="按类别过滤"),
    enabled_only: bool = Query(False, description="仅显示有效的关键字"),
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取关键字列表"""
    query = db.query(Keyword)

    if category:
        query = query.filter(Keyword.category == category)

    if enabled_only:
        query = query.filter(Keyword.is_valid == True)

    keywords = query.order_by(Keyword.category, Keyword.name).all()

    # 转换为字典格式
    result = []
    for kw in keywords:
        # 处理 parameter_schema: 可能是字符串（SQLite）或字典（PostgreSQL）
        param_schema = kw.parameter_schema
        if param_schema:
            if isinstance(param_schema, str):
                try:
                    param_schema = json.loads(param_schema)
                except json.JSONDecodeError:
                    param_schema = {}
            elif not isinstance(param_schema, dict):
                param_schema = dict(param_schema) if param_schema else {}
        else:
            param_schema = {}

        result.append({
            "id": str(kw.id),
            "name": kw.name,
            "category": kw.category,
            "description": kw.description,
            "parameter_schema": param_schema,
            "enabled": kw.is_valid,
            "examples": []  # TODO: 从其他来源获取示例
        })

    return result


@router.get("/categories")
@cache_response(ttl=600)  # 缓存 10 分钟（类别很少变化）
async def get_categories(
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取所有关键字类别"""
    categories = db.query(Keyword.category).distinct().all()
    return [cat[0] for cat in categories]


@router.get("/{keyword_id}")
async def get_keyword(
    keyword_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取单个关键字详情"""
    keyword = validate_and_fetch(db, Keyword, keyword_id, "关键字")

    # 处理 parameter_schema: 可能是字符串（SQLite）或字典（PostgreSQL）
    param_schema = keyword.parameter_schema
    if param_schema:
        if isinstance(param_schema, str):
            try:
                param_schema = json.loads(param_schema)
            except json.JSONDecodeError:
                param_schema = {}
        elif not isinstance(param_schema, dict):
            param_schema = dict(param_schema) if param_schema else {}
    else:
        param_schema = {}

    return {
        "id": str(keyword.id),
        "name": keyword.name,
        "category": keyword.category,
        "description": keyword.description,
        "parameter_schema": param_schema,
        "enabled": keyword.is_valid,
        "examples": []
    }


@router.post("/")
@router.post("")
async def create_keyword(
    keyword: KeywordCreate,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """创建关键字"""
    existing = db.query(Keyword).filter(Keyword.name == keyword.name).first()
    if existing:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"关键字 '{keyword.name}' 已存在")

    new_kw = Keyword(
        name=keyword.name,
        keyword_type=keyword.keyword_type,
        category=keyword.category,
        description=keyword.description,
        icon=keyword.icon,
        parameter_schema=keyword.parameter_schema,
        return_schema=keyword.return_schema,
        code_content=keyword.code_content,
        created_by=user.id,
    )
    db.add(new_kw)
    db.commit()
    db.refresh(new_kw)

    invalidate_pattern("list_*")
    logger.info(f"关键字已创建: {new_kw.name} (id={new_kw.id})")
    return {
        "id": str(new_kw.id),
        "name": new_kw.name,
        "keyword_type": new_kw.keyword_type,
        "category": new_kw.category,
        "description": new_kw.description,
        "icon": new_kw.icon,
        "parameter_schema": new_kw.parameter_schema,
        "return_schema": new_kw.return_schema,
        "code_content": new_kw.code_content,
        "is_valid": new_kw.is_valid,
        "created_at": new_kw.created_at.isoformat() if new_kw.created_at else None,
    }


@router.put("/{keyword_id}")
async def update_keyword(
    keyword_id: str,
    keyword: KeywordCreate,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """更新关键字"""
    kw = validate_and_fetch(db, Keyword, keyword_id, "关键字")

    if keyword.name != kw.name:
        existing = db.query(Keyword).filter(Keyword.name == keyword.name).first()
        if existing:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"关键字 '{keyword.name}' 已存在")

    kw.name = keyword.name
    kw.keyword_type = keyword.keyword_type
    kw.category = keyword.category
    kw.description = keyword.description
    kw.icon = keyword.icon
    kw.parameter_schema = keyword.parameter_schema
    kw.return_schema = keyword.return_schema
    kw.code_content = keyword.code_content

    db.commit()
    db.refresh(kw)

    invalidate_pattern("list_*")
    logger.info(f"关键字已更新: {kw.name} (id={kw.id})")
    return {
        "id": str(kw.id),
        "name": kw.name,
        "keyword_type": kw.keyword_type,
        "category": kw.category,
        "description": kw.description,
        "icon": kw.icon,
        "parameter_schema": kw.parameter_schema,
        "return_schema": kw.return_schema,
        "code_content": kw.code_content,
        "is_valid": kw.is_valid,
        "created_at": kw.created_at.isoformat() if kw.created_at else None,
    }


@router.delete("/{keyword_id}")
async def delete_keyword(
    keyword_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """删除关键字"""
    kw = validate_and_fetch(db, Keyword, keyword_id, "关键字")
    db.delete(kw)
    db.commit()

    invalidate_pattern("list_*")
    logger.info(f"关键字已删除: {kw.name} (id={kw.id})")
    return {"message": f"关键字 '{kw.name}' 已删除"}
