"""
审计日志 API

提供审计日志查询和导出功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from ..core.database import get_db
from ..models.audit import AuditLog
from ..models.user import User
from ..core.security import get_authenticated_user, require_admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["审计日志"])


@router.get("/logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    action: Optional[str] = Query(None, description="操作类型过滤"),
    resource_type: Optional[str] = Query(None, description="资源类型过滤"),
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取审计日志列表

    需要管理员权限
    """
    # 构建查询
    query = db.query(AuditLog)

    # 应用过滤条件
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)

    # 排序和分页
    query = query.order_by(AuditLog.timestamp.desc())
    logs = query.offset(skip).limit(limit).all()

    # 获取总数
    total = query.count()

    return {
        "total": total,
        "logs": [log.to_dict() for log in logs]
    }


@router.get("/logs/stats")
async def get_audit_stats(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取审计日志统计信息

    需要管理员权限
    """
    # 统计信息
    total_logs = db.query(AuditLog).count()

    # 最近7天的日志数
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_logs = db.query(AuditLog).filter(AuditLog.timestamp >= seven_days_ago).count()

    # 按操作类型统计
    from sqlalchemy import func
    action_stats = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).all()

    # 按资源类型统计
    resource_stats = db.query(
        AuditLog.resource_type,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.resource_type).all()

    # 失败操作统计
    failed_logs = db.query(AuditLog).filter(AuditLog.success == False).count()

    return {
        "total_logs": total_logs,
        "recent_logs": recent_logs,
        "failed_logs": failed_logs,
        "action_stats": [{"action": action, "count": count} for action, count in action_stats],
        "resource_stats": [{"resource_type": resource, "count": count} for resource, count in resource_stats]
    }


@router.get("/logs/user/{user_id}")
async def get_user_audit_logs(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    获取特定用户的审计日志

    用户可以查看自己的日志，管理员可以查看所有用户的日志
    """
    # 检查权限（只能查看自己的日志，除非是管理员）
    if current_user.role != "admin" and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="权限不足")

    # 查询日志
    query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    total = query.count()

    return {
        "total": total,
        "logs": [log.to_dict() for log in logs]
    }
