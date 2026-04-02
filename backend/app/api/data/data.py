from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...core.database import get_db
from ...models.test_data import TestData
from ...schemas.data import TestDataCreate, TestDataResponse

router = APIRouter(prefix="/data", tags=["测试数据"])


@router.post("/", response_model=TestDataResponse)
async def create_data(
    data: TestDataCreate,
    project_id: str,
    db: Session = Depends(get_db)
):
    new_data = TestData(**data.dict(), project_id=project_id)
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    return new_data


@router.get("/", response_model=List[TestDataResponse])
async def list_data(project_id: str, db: Session = Depends(get_db)):
    data = db.query(TestData).filter(TestData.project_id == project_id).all()
    return data


@router.get("/{data_id}", response_model=TestDataResponse)
async def get_data(data_id: str, db: Session = Depends(get_db)):
    data = db.query(TestData).filter(TestData.id == data_id).first()
    if not data:
        raise HTTPException(status_code=404, detail="数据不存在")
    return data


@router.put("/{data_id}", response_model=TestDataResponse)
async def update_data(
    data_id: str,
    data_update: TestDataCreate,
    db: Session = Depends(get_db)
):
    data = db.query(TestData).filter(TestData.id == data_id).first()
    if not data:
        raise HTTPException(status_code=404, detail="数据不存在")

    for field, value in data_update.dict(exclude_unset=True).items():
        setattr(data, field, value)

    db.commit()
    db.refresh(data)
    return data


@router.delete("/{data_id}")
async def delete_data(data_id: str, db: Session = Depends(get_db)):
    data = db.query(TestData).filter(TestData.id == data_id).first()
    if not data:
        raise HTTPException(status_code=404, detail="数据不存在")

    db.delete(data)
    db.commit()
    return {"message": "数据已删除"}