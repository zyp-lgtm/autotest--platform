"""
定时任务模型

提供定时任务管理功能，支持 cron 表达式调度
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class ScheduledJob(Base):
    """
    定时任务模型

    支持 cron 表达式调度和失败重试机制
    """
    __tablename__ = "scheduled_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)  # 定时任务名称
    task_id = Column(UUID(as_uuid=True), ForeignKey("ui_tasks.id"), nullable=False)
    cron_expression = Column(String(100))  # cron 表达式
    enabled = Column(Boolean, default=True)  # 是否启用
    next_run_at = Column(DateTime(timezone=True))  # 下次运行时间
    last_run_at = Column(DateTime(timezone=True))  # 上次运行时间
    retry_count = Column(Integer, default=0)  # 当前重试次数
    max_retries = Column(Integer, default=3)  # 最大重试次数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships - 使用字符串引用外键避免映射冲突
    project = relationship("Project", foreign_keys="ScheduledJob.project_id")
    task = relationship("UITask", foreign_keys="ScheduledJob.task_id")

    def __repr__(self):
        return f"<ScheduledJob(id={self.id}, name={self.name}, enabled={self.enabled})>"
