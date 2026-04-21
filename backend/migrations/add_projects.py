#!/usr/bin/env python3
"""
创建 projects 表
"""
import sqlite3
import sys

def create_projects_table():
    conn = sqlite3.connect('test_platform.db')
    cursor = conn.cursor()

    try:
        # 创建 projects 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                owner_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users (id)
            )
        """)
        print("✓ 创建 projects 表成功")

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_projects_owner_id
            ON projects(owner_id)
        """)
        print("✓ 创建索引成功")

        conn.commit()
        print("\n✓ 数据库迁移完成！")
        return True

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("数据库迁移: 添加 projects 表")
    print("=" * 60)
    print()

    success = create_projects_table()

    if success:
        print("\n" + "=" * 60)
        print("✓ 迁移成功")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ 迁移失败")
        print("=" * 60)
        sys.exit(1)
