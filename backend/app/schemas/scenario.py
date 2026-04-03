from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import uuid


class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    scenario_type: str = "ui"
    tags: List[str] = []


class ScenarioCreate(ScenarioBase):
    # execution_order 由系统自动计算，不在创建时指定
    pass


class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scenario_type: Optional[str] = None
    execution_order: Optional[int] = None
    tags: Optional[List[str]] = None


class ScenarioResponse(ScenarioBase):
    id: uuid.UUID
    task_id: uuid.UUID
    project_id: uuid.UUID
    execution_order: int
    case_ids: List[uuid.UUID] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
