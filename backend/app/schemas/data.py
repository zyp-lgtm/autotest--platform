from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class TestDataBase(BaseModel):
    data_name: str = Field(..., min_length=1, max_length=100, description="数据名称")
    data_value: str = Field(..., max_length=10000, description="数据值")
    data_type: str = Field(default="string", max_length=50, description="数据类型")
    description: Optional[str] = Field(None, max_length=1000, description="描述")
    tags: list = Field(default_factory=list, description="标签列表")
    is_sensitive: bool = False


class TestDataCreate(TestDataBase):
    pass


class TestDataResponse(TestDataBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True