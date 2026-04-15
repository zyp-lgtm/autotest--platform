from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import uuid


class StepBase(BaseModel):
    step_order: int
    keyword_id: uuid.UUID
    step_name: str = Field(..., max_length=200, description="步骤名称")
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
    name: str = Field(..., min_length=1, max_length=100, description="用例名称")
    description: Optional[str] = Field(None, max_length=1000, description="用例描述")
    priority: str = "P2"
    tags: List[str] = Field(default_factory=list, description="标签列表")


class CaseCreate(CaseBase):
    pass


class CaseResponse(CaseBase):
    id: uuid.UUID
    step_ids: List[uuid.UUID] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ScenarioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="场景名称")
    description: Optional[str] = Field(None, max_length=1000, description="场景描述")
    execution_order: int = 0
    tags: List[str] = Field(default_factory=list, description="标签列表")


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioResponse(ScenarioBase):
    id: uuid.UUID
    case_ids: List[uuid.UUID] = []
    created_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="任务名称")
    description: Optional[str] = Field(None, max_length=1000, description="任务描述")
    tags: List[str] = Field(default_factory=list, description="标签列表")


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    name: Optional[str] = Field(None, max_length=100, description="任务名称")
    description: Optional[str] = Field(None, max_length=1000, description="任务描述")
    tags: Optional[List[str]] = None
    scenario_ids: Optional[List[uuid.UUID]] = None


class TaskResponse(TaskBase):
    id: uuid.UUID
    scenario_ids: List[uuid.UUID] = []
    created_at: datetime

    class Config:
        from_attributes = True