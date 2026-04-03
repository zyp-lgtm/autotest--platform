"""
测试执行相关的 Pydantic schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid


class StepExecutionLog(BaseModel):
    """步骤执行日志"""
    timestamp: str
    level: str  # info, warning, error
    message: str


class StepExecutionResponse(BaseModel):
    """步骤执行响应"""
    id: uuid.UUID
    step_id: uuid.UUID
    step_name: str
    step_order: int
    keyword_name: str
    category: str
    status: str
    result: Optional[str] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    logs: List[Dict[str, Any]] = []
    output: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class CaseExecutionResponse(BaseModel):
    """用例执行响应"""
    id: uuid.UUID
    case_id: uuid.UUID
    status: str
    result: Optional[str] = None
    duration: Optional[float] = None
    total_steps: int
    passed_steps: int
    failed_steps: int
    error_message: Optional[str] = None
    step_executions: List[StepExecutionResponse] = []

    class Config:
        from_attributes = True


class ScenarioExecutionResponse(BaseModel):
    """场景执行响应"""
    id: uuid.UUID
    scenario_id: uuid.UUID
    status: str
    result: Optional[str] = None
    duration: Optional[float] = None
    execution_order: int
    total_cases: int
    total_steps: int
    passed_steps: int
    failed_steps: int
    case_executions: List[CaseExecutionResponse] = []

    class Config:
        from_attributes = True


class TestExecutionResponse(BaseModel):
    """任务执行响应"""
    id: uuid.UUID
    task_id: uuid.UUID
    project_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    status: str
    result: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None

    # 统计
    total_scenarios: int
    total_cases: int
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int

    error_message: Optional[str] = None
    scenario_executions: List[ScenarioExecutionResponse] = []

    created_at: datetime

    class Config:
        from_attributes = True


class ExecutionRequest(BaseModel):
    """执行请求"""
    task_id: uuid.UUID
    execution_config: Optional[Dict[str, Any]] = None
    browser_config: Optional[Dict[str, Any]] = None
    environment: Optional[str] = "development"
