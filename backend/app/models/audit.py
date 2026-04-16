"""
审计日志模型

记录系统中的敏感操作，包括：
- 用户认证操作（登录、登出）
- 数据修改操作（创建、更新、删除）
- 测试执行操作
- 权限变更操作
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from ..core.database import Base


class AuditLog(Base):
    """
    审计日志模型

    记录所有敏感操作以便后续审计和追踪
    """

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 操作信息
    action = Column(String(50), nullable=False, index=True, comment="操作类型：login/logout/create/update/delete/execute")
    resource_type = Column(String(50), nullable=False, index=True, comment="资源类型：user/project/scenario/case/task/data/keyword")
    resource_id = Column(String(100), nullable=True, index=True, comment="资源ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True, comment="操作用户ID")

    # 操作详情
    details = Column(JSON, nullable=True, comment="操作详情（JSON格式）")
    ip_address = Column(String(50), nullable=True, comment="客户端IP地址")
    user_agent = Column(String(500), nullable=True, comment="客户端User-Agent")
    success = Column(Boolean, nullable=False, default=True, comment="操作是否成功")

    # 审计信息
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, comment="操作时间戳")
    session_id = Column(String(100), nullable=True, comment="会话ID")

    # 关系
    user = relationship("User", back_populates="audit_logs")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": str(self.id),
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": str(self.user_id) if self.user_id else None,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "session_id": self.session_id
        }
