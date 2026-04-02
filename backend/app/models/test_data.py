from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class TestData(Base):
    __tablename__ = "test_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    data_name = Column(String(100), nullable=False)
    data_value = Column(Text, nullable=False)
    data_type = Column(Enum("string", "number", "boolean", "json", name="data_types"), default="string")
    description = Column(Text)
    tags = Column(ARRAY(String), default=[])
    is_sensitive = Column(Boolean, default=False)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="test_data")
    project = relationship("Project", back_populates="test_data")