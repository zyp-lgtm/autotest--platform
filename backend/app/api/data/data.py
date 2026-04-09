"""
测试数据 API
提供测试数据的 CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import uuid

from ...models.test_data import TestData
from ...schemas.data import TestDataCreate
from ...core.database import get_db
from ...core.security import oauth2_scheme, verify_token

router = APIRouter(prefix="/data", tags=["测试数据"])


@router.post("/")
async def create_data(
    data: TestDataCreate,
    project_id: str = Query(..., description="项目ID"),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """创建测试数据"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        project_id_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的项目ID格式")

    new_data = TestData(**data.dict(), project_id=project_id_uuid)
    db.add(new_data)
    db.commit()
    db.refresh(new_data)

    # 手动序列化
    return {
        "id": str(new_data.id),
        "project_id": str(new_data.project_id),
        "name": new_data.name,
        "description": new_data.description,
        "data_type": new_data.data_type,
        "content": new_data.content,
        "tags": list(new_data.tags) if new_data.tags else [],
        "created_at": new_data.created_at.isoformat() if new_data.created_at else None,
        "updated_at": new_data.updated_at.isoformat() if new_data.updated_at else None
    }


@router.get("/")
async def list_data(
    project_id: str = Query(..., description="项目ID"),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取项目的所有测试数据"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        project_id_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的项目ID格式")

    data_list = db.query(TestData).filter(
        TestData.project_id == project_id_uuid
    ).order_by(TestData.created_at.desc()).all()

    # 手动序列化
    result = []
    for data_item in data_list:
        result.append({
            "id": str(data_item.id),
            "project_id": str(data_item.project_id),
            "name": data_item.name,
            "description": data_item.description,
            "data_type": data_item.data_type,
            "content": data_item.content,
            "tags": list(data_item.tags) if data_item.tags else [],
            "created_at": data_item.created_at.isoformat() if data_item.created_at else None,
            "updated_at": data_item.updated_at.isoformat() if data_item.updated_at else None
        })
    return result


@router.get("/{data_id}")
async def get_data(
    data_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取单个测试数据详情"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        data_id_uuid = uuid.UUID(data_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的数据ID格式")

    data_item = db.query(TestData).filter(TestData.id == data_id_uuid).first()
    if not data_item:
        raise HTTPException(status_code=404, detail="数据不存在")

    # 手动序列化
    return {
        "id": str(data_item.id),
        "project_id": str(data_item.project_id),
        "name": data_item.name,
        "description": data_item.description,
        "data_type": data_item.data_type,
        "content": data_item.content,
        "tags": list(data_item.tags) if data_item.tags else [],
        "created_at": data_item.created_at.isoformat() if data_item.created_at else None,
        "updated_at": data_item.updated_at.isoformat() if data_item.updated_at else None
    }


@router.put("/{data_id}")
async def update_data(
    data_id: str,
    data_update: TestDataCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新测试数据"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        data_id_uuid = uuid.UUID(data_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的数据ID格式")

    data_item = db.query(TestData).filter(TestData.id == data_id_uuid).first()
    if not data_item:
        raise HTTPException(status_code=404, detail="数据不存在")

    # 更新非空字段
    update_data = data_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(data_item, field, value)

    db.commit()
    db.refresh(data_item)

    # 手动序列化
    return {
        "id": str(data_item.id),
        "project_id": str(data_item.project_id),
        "name": data_item.name,
        "description": data_item.description,
        "data_type": data_item.data_type,
        "content": data_item.content,
        "tags": list(data_item.tags) if data_item.tags else [],
        "created_at": data_item.created_at.isoformat() if data_item.created_at else None,
        "updated_at": data_item.updated_at.isoformat() if data_item.updated_at else None
    }


@router.delete("/{data_id}")
async def delete_data(
    data_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """删除测试数据"""
    # 验证用户身份
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    try:
        data_id_uuid = uuid.UUID(data_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的数据ID格式")

    data_item = db.query(TestData).filter(TestData.id == data_id_uuid).first()
    if not data_item:
        raise HTTPException(status_code=404, detail="数据不存在")

    db.delete(data_item)
    db.commit()
    return {"message": "数据已删除"}
