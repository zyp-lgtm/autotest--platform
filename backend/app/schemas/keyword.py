from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class KeywordBase(BaseModel):
    name: str
    keyword_type: str = "system"
    category: str
    description: Optional[str] = None
    icon: Optional[str] = None
    parameter_schema: dict = {}
    return_schema: dict = {}


class KeywordCreate(KeywordBase):
    code_content: Optional[str] = None


class KeywordResponse(KeywordBase):
    id: uuid.UUID
    is_valid: bool
    created_at: datetime

    class Config:
        from_attributes = True