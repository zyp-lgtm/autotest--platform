"""
添加审计日志表

迁移脚本：创建 audit_logs 表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine, Base
from app.models.audit import AuditLog


def upgrade():
    """创建审计日志表"""
    print("创建 audit_logs 表...")

    # 创建表
    Base.metadata.create_all(bind=engine, tables=[AuditLog.__table__])

    # 创建索引
    with engine.connect() as conn:
        # 为 action 字段创建索引（如果不存在）
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_audit_logs_action
            ON audit_logs (action)
        """))

        # 为 resource_type 字段创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_audit_logs_resource_type
            ON audit_logs (resource_type)
        """))

        # 为 resource_id 字段创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_audit_logs_resource_id
            ON audit_logs (resource_id)
        """))

        # 为 user_id 字段创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id
            ON audit_logs (user_id)
        """))

        # 为 timestamp 字段创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_audit_logs_timestamp
            ON audit_logs (timestamp)
        """))

        conn.commit()

    print("✅ audit_logs 表创建成功")


def downgrade():
    """删除审计日志表"""
    print("删除 audit_logs 表...")

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS audit_logs"))
        conn.commit()

    print("✅ audit_logs 表删除成功")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="审计日志表迁移")
    parser.add_argument("--downgrade", action="store_true", help="回滚迁移")
    args = parser.parse_args()

    if args.downgrade:
        downgrade()
    else:
        upgrade()
