"""
环境配置模型

提供多环境配置管理功能，支持开发、测试、生产等不同环境
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class Environment(Base):
    """
    环境配置模型

    支持多环境配置（dev/test/prod等）和环境变量管理
    """
    __tablename__ = "environments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False)  # 环境名称：dev/test/prod 等
    base_url = Column(String(500))  # 环境 URL
    variables = Column(JSON, default=dict)  # 环境变量
    is_default = Column(Boolean, default=False)  # 是否为默认环境
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships - 使用字符串引用外键避免映射冲突
    project = relationship("Project", foreign_keys="Environment.project_id")

    def __repr__(self):
        return f"<Environment(id={self.id}, name={self.name}, project_id={self.project_id})>"
