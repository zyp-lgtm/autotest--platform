"""
数据库健康检查和自动初始化
确保数据库在应用启动时可用
"""
import os
from pathlib import Path
from sqlalchemy import inspect, text
from .database import engine, Base
import logging

logger = logging.getLogger(__name__)


def database_exists() -> bool:
    """检查数据库文件是否存在"""
    db_path = os.path.abspath("test_platform.db")
    return os.path.exists(db_path) and os.path.getsize(db_path) > 0


def is_database_initialized() -> bool:
    """检查数据库是否已初始化（是否有表）"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return len(tables) > 0
    except Exception as e:
        logger.error(f"检查数据库初始化状态失败: {e}")
        return False


def initialize_database():
    """初始化数据库（创建表和基础数据）"""
    try:
        logger.info("开始初始化数据库...")

        # 1. 创建所有表
        from ..models import (
            user, project, ui_task, keyword,
            execution
        )

        Base.metadata.create_all(bind=engine)
        logger.info("✓ 数据库表创建完成")

        # 2. 创建测试用户
        from ..models.user import User
        from sqlalchemy.orm import Session

        with Session(engine) as db:
            # 检查是否已有用户
            existing_user = db.query(User).filter(User.username == "demo").first()
            if not existing_user:
                demo_user = User(
                    username="demo",
                    email="demo@example.com",
                    full_name="演示用户",
                    hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY IWwD3Kq"  # demo123
                )
                db.add(demo_user)
                db.commit()
                logger.info("✓ 测试用户创建完成")
            else:
                logger.info("✓ 测试用户已存在")

        logger.info("✓ 数据库初始化完成")
        return True

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}", exc_info=True)
        return False


def check_database_health() -> dict:
    """
    检查数据库健康状态

    Returns:
        dict: {
            "healthy": bool,
            "message": str,
            "details": dict
        }
    """
    details = {}

    # 检查 1: 数据库文件是否存在
    if not database_exists():
        return {
            "healthy": False,
            "message": "数据库文件不存在",
            "details": {
                "error": "database_not_found",
                "suggestion": "运行数据库初始化"
            }
        }

    # 检查 2: 数据库是否已初始化
    if not is_database_initialized():
        return {
            "healthy": False,
            "message": "数据库未初始化",
            "details": {
                "error": "database_not_initialized",
                "suggestion": "需要创建表和基础数据"
            }
        }

    # 检查 3: 能否连接数据库
    try:
        with engine.connect() as conn:
            # 执行简单查询测试连接
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

        details["connection"] = "ok"

        # 检查关键表是否存在
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        required_tables = [
            "users", "projects", "ui_tasks", "ui_scenarios",
            "ui_test_cases", "ui_test_steps", "keywords"
        ]

        missing_tables = [t for t in required_tables if t not in tables]
        if missing_tables:
            return {
                "healthy": False,
                "message": f"缺少关键表: {', '.join(missing_tables)}",
                "details": {
                    "missing_tables": missing_tables,
                    "existing_tables": tables
                }
            }

        details["tables"] = len(tables)

        # 检查基础数据
        from sqlalchemy.orm import Session
        with Session(engine) as db:
            from ..models.user import User
            user_count = db.query(User).count()
            details["users"] = user_count

        return {
            "healthy": True,
            "message": "数据库健康",
            "details": details
        }

    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return {
            "healthy": False,
            "message": f"数据库连接失败: {str(e)}",
            "details": {
                "error": str(e)
            }
        }


def ensure_database_ready() -> bool:
    """
    确保数据库就绪，如果未初始化则自动初始化

    Returns:
        bool: 数据库是否就绪
    """
    health = check_database_health()

    if health["healthy"]:
        logger.info("✓ 数据库健康，无需初始化")
        return True

    # 数据库不健康，尝试初始化
    logger.warning(f"数据库不健康: {health['message']}")
    logger.info("尝试自动初始化数据库...")

    success = initialize_database()

    if success:
        logger.info("✓ 数据库自动初始化成功")
        return True
    else:
        logger.error("✗ 数据库自动初始化失败")
        return False
