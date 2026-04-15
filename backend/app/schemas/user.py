from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: str | None = Field(None, max_length=100, description="全名")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="密码")


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    role: str
    created_at: datetime

    class Config:
        from_attributes = True