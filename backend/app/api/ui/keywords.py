"""
关键字 API
提供关键字查询接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from ...models.keyword import Keyword
from ...core.database import get_db

router = APIRouter(prefix="/ui/keywords", tags=["UI关键字"])


@router.get("/", response_model=List[dict])
async def list_keywords(
    category: Optional[str] = Query(None, description="按类别过滤"),
    enabled_only: bool = Query(False, description="仅显示有效的关键字"),
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
        result.append({
            "id": str(kw.id),
            "name": kw.name,
            "category": kw.category,
            "description": kw.description,
            "parameter_schema": dict(kw.parameter_schema) if kw.parameter_schema else {},
            "enabled": kw.is_valid,
            "examples": []  # TODO: 从其他来源获取示例
        })

    return result


@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """获取所有关键字类别"""
    categories = db.query(Keyword.category).distinct().all()
    return [cat[0] for cat in categories]


@router.get("/{keyword_id}")
async def get_keyword(keyword_id: str, db: Session = Depends(get_db)):
    """获取单个关键字详情"""
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        return {"error": "关键字不存在"}

    return {
        "id": str(keyword.id),
        "name": keyword.name,
        "category": keyword.category,
        "description": keyword.description,
        "parameter_schema": dict(keyword.parameter_schema) if keyword.parameter_schema else {},
        "enabled": keyword.is_valid,
        "examples": []
    }
