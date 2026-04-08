from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UUID, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class APITask(Base):
    __tablename__ = "api_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    task_type = Column(String(10), default="api")
    scenario_ids = Column(JSON, default=[])

    execution_config = Column(JSON, default={})
    report_config = Column(JSON, default={})
    tags = Column(JSON, default=list)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    scenarios = relationship("APIScenario", back_populates="task")


class APIScenario(Base):
    __tablename__ = "api_scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("api_tasks.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    scenario_type = Column(String(10), default="api")
    case_ids = Column(JSON, default=[])
    execution_order = Column(Integer, default=0)
    tags = Column(JSON, default=list)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    task = relationship("APITask", back_populates="scenarios")
    cases = relationship("APICase", back_populates="scenario")


class APICase(Base):
    __tablename__ = "api_test_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("api_scenarios.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    case_type = Column(String(10), default="api")
    step_ids = Column(JSON, default=[])

    data_bindings = Column(JSON, default={})
    tags = Column(JSON, default=list)
    priority = Column(String(10), default="P2")

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    scenario = relationship("APIScenario", back_populates="cases")
    steps = relationship("APIStep", back_populates="case")


class APIStep(Base):
    __tablename__ = "api_test_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("api_test_cases.id"), nullable=False)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("api_scenarios.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("api_tasks.id"), nullable=False)

    step_order = Column(Integer, nullable=False)
    keyword_id = Column(UUID(as_uuid=True), ForeignKey("keywords.id"), nullable=False)
    step_name = Column(String(200), nullable=False)
    step_type = Column(String(10), default="api")

    parameters = Column(JSON, default={})
    enabled = Column(Boolean, default=True)
    continue_on_failure = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    case = relationship("APICase", back_populates="steps")