from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    keyword_type = Column(Enum("system", "business", name="keyword_types"), nullable=False)
    category = Column(Enum("api", "ui", "assertion", "extract", "data", name="keyword_categories"), nullable=False)
    description = Column(Text)
    icon = Column(String(50))

    # 参数和返回值模式
    parameter_schema = Column(JSON, default={})
    return_schema = Column(JSON, default={})

    # 业务关键字代码
    code_content = Column(Text)
    is_valid = Column(Boolean, default=True)

    # 系统关键字不关联项目
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User")
    project = relationship("Project")