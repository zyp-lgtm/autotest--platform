#!/usr/bin/env python3
"""
添加测试数据管理功能

创建以下表：
- test_data: 测试数据表
- data_bindings: 数据绑定表
"""
import sqlite3
import sys
import uuid
import json


def create_test_data_tables():
    """创建测试数据管理表"""
    conn = sqlite3.connect('test_platform.db')
    cursor = conn.cursor()

    try:
        print("=" * 60)
        print("数据库迁移: 添加测试数据管理功能")
        print("=" * 60)
        print()

        # 1. 创建 test_data 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_data (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                data_type TEXT NOT NULL,
                data JSON NOT NULL,
                tags JSON DEFAULT '[]',
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        """)
        print("✓ 创建 test_data 表成功")

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_test_data_project_id
            ON test_data(project_id)
        """)
        print("✓ 创建 test_data 索引成功")

        # 2. 创建 data_bindings 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_bindings (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                data_id TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES ui_cases (id),
                FOREIGN KEY (data_id) REFERENCES test_data (id)
            )
        """)
        print("✓ 创建 data_bindings 表成功")

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_data_bindings_case_id
            ON data_bindings(case_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_data_bindings_data_id
            ON data_bindings(data_id)
        """)
        print("✓ 创建 data_bindings 索引成功")

        conn.commit()
        print()
        print("=" * 60)
        print("✓ 测试数据管理功能迁移完成！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = create_test_data_tables()

    if success:
        # 验证表已创建
        conn = sqlite3.connect('test_platform.db')
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('test_data', 'data_bindings')")
        tables = cursor.fetchall()

        print()
        print("已创建的表:")
        print("-" * 60)
        for table in tables:
            print(f"  ✓ {table[0]}")

        conn.close()
        sys.exit(0)
    else:
        sys.exit(1)
