"""
测试数据模型

提供测试数据管理和数据驱动测试功能
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from datetime import timezone
from ..core.database import Base


class TestData(Base):
    """
    测试数据模型

    支持多种数据格式（JSON、CSV、SQL）用于数据驱动测试
    """
    __tablename__ = "test_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    data_type = Column(String(50), nullable=False)  # json, csv, sql
    data = Column(JSON, nullable=False, default=list)  # 存储测试数据数组
    tags = Column(JSON, default=list)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships - 使用字符串引用外键避免映射冲突
    creator = relationship("User", foreign_keys="TestData.created_by")
    project = relationship("Project", foreign_keys="TestData.project_id")
    bindings = relationship("DataBinding", foreign_keys="DataBinding.data_id", cascade="all, delete-orphan")


class DataBinding(Base):
    """
    数据绑定模型

    将测试数据绑定到测试用例，实现数据驱动测试
    """
    __tablename__ = "data_bindings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("ui_test_cases.id"), nullable=False)
    data_id = Column(UUID(as_uuid=True), ForeignKey("test_data.id"), nullable=False)
    enabled = Column(Integer, default=1)  # 布尔值，1=启用，0=禁用
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships - 使用字符串引用外键避免映射冲突
    test_case = relationship("UICase", foreign_keys="DataBinding.case_id")
    test_data = relationship("TestData", foreign_keys="DataBinding.data_id")

    def __repr__(self):
        return f"<DataBinding(case_id={self.case_id}, data_id={self.data_id}, enabled={self.enabled})>"