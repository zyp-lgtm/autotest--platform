from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    role: str
    created_at: datetime

    class Config:
        from_attributes = True