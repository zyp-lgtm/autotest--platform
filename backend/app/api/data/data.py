"""
测试数据 API
提供测试数据的 CRUD 操作
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from ...models.test_data import TestData
from ...models.user import User
from ...schemas.data import TestDataCreate
from ...core.database import get_db
from ...core.security import get_authenticated_user
from ..utils import validate_and_fetch, serialize_model

router = APIRouter(prefix="/data", tags=["测试数据"])


@router.post("/")
async def create_data(
    data: TestDataCreate,
    project_id: str = Query(..., description="项目ID"),
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """创建测试数据"""
    from ...utils import validate_uuid
    project_id_uuid = validate_uuid(project_id, "项目")

    new_data = TestData(**data.dict(), project_id=project_id_uuid)
    db.add(new_data)
    db.commit()
    db.refresh(new_data)

    return serialize_model(new_data)


@router.get("/")
async def list_data(
    project_id: str = Query(..., description="项目ID"),
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取项目的所有测试数据"""
    from ...utils import validate_uuid
    project_id_uuid = validate_uuid(project_id, "项目")

    data_list = db.query(TestData).filter(
        TestData.project_id == project_id_uuid
    ).order_by(TestData.created_at.desc()).all()

    return [serialize_model(data) for data in data_list]


@router.get("/{data_id}")
async def get_data(
    data_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """获取单个测试数据详情"""
    data_item = validate_and_fetch(db, TestData, data_id, "测试数据")
    return serialize_model(data_item)


@router.put("/{data_id}")
async def update_data(
    data_id: str,
    data_update: TestDataCreate,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """更新测试数据"""
    data_item = validate_and_fetch(db, TestData, data_id, "测试数据")

    # 更新非空字段
    update_data = data_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(data_item, field, value)

    db.commit()
    db.refresh(data_item)

    return serialize_model(data_item)


@router.delete("/{data_id}")
async def delete_data(
    data_id: str,
    user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """删除测试数据"""
    data_item = validate_and_fetch(db, TestData, data_id, "测试数据")

    db.delete(data_item)
    db.commit()
    return {"message": "数据已删除"}
