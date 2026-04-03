from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import uuid


class CaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    case_type: str = "ui"
    priority: str = "P2"
    tags: List[str] = []
    data_bindings: dict = {}
    browser_config: dict = {}


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    case_type: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    data_bindings: Optional[dict] = None
    browser_config: Optional[dict] = None


class CaseResponse(CaseBase):
    id: uuid.UUID
    scenario_id: uuid.UUID
    project_id: uuid.UUID
    step_ids: List[uuid.UUID] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
