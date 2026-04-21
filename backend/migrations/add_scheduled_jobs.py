#!/usr/bin/env python3
"""
添加定时任务功能

创建 scheduled_jobs 表用于管理定时执行的任务
"""
import sqlite3
import sys


def create_scheduled_jobs_table():
    """创建定时任务表"""
    conn = sqlite3.connect('test_platform.db')
    cursor = conn.cursor()

    try:
        print("=" * 60)
        print("数据库迁移: 添加定时任务功能")
        print("=" * 60)
        print()

        # 创建 scheduled_jobs 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                task_id TEXT NOT NULL,
                cron_expression TEXT,
                enabled INTEGER DEFAULT 1,
                next_run_at TEXT,
                last_run_at TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (task_id) REFERENCES ui_tasks (id)
            )
        """)
        print("✓ 创建 scheduled_jobs 表成功")

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_project_id
            ON scheduled_jobs(project_id)
        """)
        print("✓ 创建 scheduled_jobs 索引成功")

        # 创建启用状态索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_enabled
            ON scheduled_jobs(enabled)
        """)
        print("✓ 创建启用状态索引成功")

        conn.commit()
        print()
        print("=" * 60)
        print("✓ 定时任务功能迁移完成！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = create_scheduled_jobs_table()

    if success:
        # 验证表已创建
        conn = sqlite3.connect('test_platform.db')
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scheduled_jobs'")
        tables = cursor.fetchall()

        print()
        print("已创建的表:")
        print("-" * 60)
        for table in tables:
            print(f"  ✓ {table[0]}")

        # 显示表结构
        print()
        print("表结构:")
        print("-" * 60)
        cursor.execute("PRAGMA table_info(scheduled_jobs)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]:<20} {col[2]:<20}")

        conn.close()
        sys.exit(0)
    else:
        sys.exit(1)
