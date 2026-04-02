from pydantic import BaseModel
from datetime import datetime
import uuid


class TestDataBase(BaseModel):
    data_name: str
    data_value: str
    data_type: str = "string"
    description: Optional[str] = None
    tags: list = []
    is_sensitive: bool = False


class TestDataCreate(TestDataBase):
    pass


class TestDataResponse(TestDataBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True