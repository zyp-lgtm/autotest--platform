from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid


class StepBase(BaseModel):
    step_order: int
    keyword_id: uuid.UUID
    step_name: str
    parameters: dict = {}
    enabled: bool = True
    continue_on_failure: bool = False
    screenshot_config: dict = {}


class StepCreate(StepBase):
    pass


class StepUpdate(BaseModel):
    step_order: Optional[int] = None
    keyword_id: Optional[uuid.UUID] = None
    step_name: Optional[str] = None
    parameters: Optional[dict] = None
    enabled: Optional[bool] = None
    continue_on_failure: Optional[bool] = None
    screenshot_config: Optional[dict] = None


class StepResponse(StepBase):
    id: uuid.UUID
    case_id: uuid.UUID
    scenario_id: uuid.UUID
    task_id: uuid.UUID
    step_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
