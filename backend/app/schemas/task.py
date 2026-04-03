from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import uuid


class StepBase(BaseModel):
    step_order: int
    keyword_id: uuid.UUID
    step_name: str
    parameters: dict = {}
    enabled: bool = True
    continue_on_failure: bool = False


class StepCreate(StepBase):
    pass


class StepResponse(StepBase):
    id: uuid.UUID
    keyword_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class CaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    priority: str = "P2"
    tags: List[str] = []


class CaseCreate(CaseBase):
    pass


class CaseResponse(CaseBase):
    id: uuid.UUID
    step_ids: List[uuid.UUID] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    execution_order: int = 0
    tags: List[str] = []


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioResponse(ScenarioBase):
    id: uuid.UUID
    case_ids: List[uuid.UUID] = []
    created_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    tags: List[str] = []


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    scenario_ids: Optional[List[uuid.UUID]] = None


class TaskResponse(TaskBase):
    id: uuid.UUID
    scenario_ids: List[uuid.UUID] = []
    created_at: datetime

    class Config:
        from_attributes = True