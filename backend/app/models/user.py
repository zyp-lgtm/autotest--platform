from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    role = Column(Enum("admin", "tester", "viewer", name="user_roles"), default="tester")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to projects
    projects = relationship("Project", back_populates="owner")

    # Relationships to keywords and test data
    keywords = relationship("Keyword", back_populates="creator")
    test_data = relationship("TestData", back_populates="creator")

    # Relationship to audit logs
    audit_logs = relationship("AuditLog", back_populates="user")