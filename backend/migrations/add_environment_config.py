#!/usr/bin/env python3
"""
添加环境配置管理功能

创建 environments 表用于管理不同环境的配置
"""
import sqlite3
import sys


def create_environments_table():
    """创建环境配置表"""
    conn = sqlite3.connect('test_platform.db')
    cursor = conn.cursor()

    try:
        print("=" * 60)
        print("数据库迁移: 添加环境配置管理功能")
        print("=" * 60)
        print()

        # 创建 environments 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS environments (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                base_url TEXT,
                variables JSON DEFAULT '{}',
                is_default INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        print("✓ 创建 environments 表成功")

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_environments_project_id
            ON environments(project_id)
        """)
        print("✓ 创建 environments 索引成功")

        # 创建唯一索引（每个项目内环境名称唯一）
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_environments_project_name
            ON environments(project_id, name)
        """)
        print("✓ 创建环境名称唯一索引成功")

        conn.commit()
        print()
        print("=" * 60)
        print("✓ 环境配置管理功能迁移完成！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = create_environments_table()

    if success:
        # 验证表已创建
        conn = sqlite3.connect('test_platform.db')
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='environments'")
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
        cursor.execute("PRAGMA table_info(environments)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]:<20} {col[2]:<20}")

        conn.close()
        sys.exit(0)
    else:
        sys.exit(1)
