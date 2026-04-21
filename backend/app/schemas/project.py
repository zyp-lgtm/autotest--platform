"""
项目相关的 Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ProjectBase(BaseModel):
    """项目基础 schema"""
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")


class ProjectCreate(ProjectBase):
    """创建项目 schema"""
    pass


class ProjectUpdate(BaseModel):
    """更新项目 schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    """项目响应 schema"""
    id: str
    owner_id: str
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
