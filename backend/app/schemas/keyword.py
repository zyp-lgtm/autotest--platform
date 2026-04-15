from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class KeywordBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="关键字名称")
    keyword_type: str = Field(default="system", max_length=50, description="关键字类型")
    category: str = Field(..., max_length=50, description="分类")
    description: Optional[str] = Field(None, max_length=1000, description="描述")
    icon: Optional[str] = Field(None, max_length=100, description="图标")
    parameter_schema: dict = Field(default_factory=dict, description="参数模式")
    return_schema: dict = Field(default_factory=dict, description="返回模式")


class KeywordCreate(KeywordBase):
    code_content: Optional[str] = Field(None, max_length=50000, description="代码内容")


class KeywordResponse(KeywordBase):
    id: uuid.UUID
    is_valid: bool
    created_at: datetime

    class Config:
        from_attributes = True