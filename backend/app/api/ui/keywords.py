"""
关键字 API
提供关键字查询接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from ...models.keyword import Keyword
from ...models.user import User
from ...core.database import get_db
from ...core.security import get_authenticated_user
from ...utils.cache import cache_response, invalidate_pattern
from ..utils import validate_and_fetch

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
