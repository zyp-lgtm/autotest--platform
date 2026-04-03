"""
测试执行记录模型
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UUID, Integer, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class TestExecution(Base):
    """测试执行记录（任务级别）"""
    __tablename__ = "test_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("ui_tasks.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # 执行信息
    status = Column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration = Column(Float)  # 执行时长（秒）

    # 统计信息
    total_scenarios = Column(Integer, default=0)
    total_cases = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    passed_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)
    skipped_steps = Column(Integer, default=0)

    # 执行配置
    execution_config = Column(JSON, default={})
    browser_config = Column(JSON, default={})
    environment = Column(String(50), default="development")

    # 结果
    result = Column(String(20))  # pass, fail, error
    error_message = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联
    scenario_executions = relationship("ScenarioExecution", back_populates="task_execution", cascade="all, delete-orphan")


class ScenarioExecution(Base):
    """场景执行记录"""
    __tablename__ = "scenario_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_execution_id = Column(UUID(as_uuid=True), ForeignKey("test_executions.id"), nullable=False)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("ui_scenarios.id"), nullable=False)

    # 执行信息
    status = Column(String(20), default="pending")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration = Column(Float)

    # 统计
    total_cases = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    passed_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)

    result = Column(String(20))
    error_message = Column(Text)
    execution_order = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联
    task_execution = relationship("TestExecution", back_populates="scenario_executions")
    case_executions = relationship("CaseExecution", back_populates="scenario_execution", cascade="all, delete-orphan")


class CaseExecution(Base):
    """用例执行记录"""
    __tablename__ = "case_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_execution_id = Column(UUID(as_uuid=True), ForeignKey("scenario_executions.id"), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("ui_test_cases.id"), nullable=False)

    # 执行信息
    status = Column(String(20), default="pending")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration = Column(Float)

    # 统计
    total_steps = Column(Integer, default=0)
    passed_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)

    result = Column(String(20))
    error_message = Column(Text)
    priority = Column(String(10))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联
    scenario_execution = relationship("ScenarioExecution", back_populates="case_executions")
    step_executions = relationship("StepExecution", back_populates="case_execution", cascade="all, delete-orphan")


class StepExecution(Base):
    """步骤执行记录"""
    __tablename__ = "step_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_execution_id = Column(UUID(as_uuid=True), ForeignKey("case_executions.id"), nullable=False)
    step_id = Column(UUID(as_uuid=True), ForeignKey("ui_test_steps.id"), nullable=False)
    keyword_id = Column(UUID(as_uuid=True), ForeignKey("keywords.id"), nullable=False)

    # 执行信息
    status = Column(String(20), default="pending")  # pending, running, passed, failed, skipped
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration = Column(Float)

    # 步骤信息
    step_name = Column(String(200), nullable=False)
    step_order = Column(Integer, nullable=False)
    keyword_name = Column(String(100))
    category = Column(String(50))  # ui, api, assertion

    # 执行参数
    parameters = Column(JSON, default={})
    continue_on_failure = Column(Boolean, default=False)

    # 结果
    result = Column(String(20))  # pass, fail, skip
    output = Column(JSON)  # 关键字执行输出
    error_message = Column(Text)
    screenshot_path = Column(String(500))  # 失败截图路径

    # 日志
    logs = Column(JSON, default=[])  # 详细日志列表
    memory_before = Column(JSON)  # 变量快照（执行前）
    memory_after = Column(JSON)   # 变量快照（执行后）

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联
    case_execution = relationship("CaseExecution", back_populates="step_executions")
