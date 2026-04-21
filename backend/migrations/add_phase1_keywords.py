#!/usr/bin/env python3
"""
添加 Phase 1 核心关键字到数据库

添加以下关键字：
- ASSERT_VISIBLE: 断言元素可见
- ASSERT_TEXT: 断言文本内容
- ASSERT_URL: 断言页面URL
- ASSERT_TITLE: 断言页面标题
- GET_TEXT: 获取元素文本
- SELECT: 下拉选择（增强版）
"""
import sqlite3
import sys
import json


def add_phase1_keywords():
    """添加 Phase 1 关键字"""
    conn = sqlite3.connect('test_platform.db')
    cursor = conn.cursor()

    # 定义新关键字
    keywords = [
        {
            "name": "ASSERT_VISIBLE",
            "keyword_type": "builtin",
            "category": "ui",
            "description": "断言元素在页面上可见",
            "parameter_schema": {
                "selector": {
                    "type": "string",
                    "required": True,
                    "description": "CSS选择器或XPath"
                },
                "timeout": {
                    "type": "integer",
                    "default": 5000,
                    "description": "超时时间（毫秒）"
                }
            },
            "enabled": True
        },
        {
            "name": "ASSERT_TEXT",
            "keyword_type": "builtin",
            "category": "ui",
            "description": "断言元素的文本内容",
            "parameter_schema": {
                "selector": {
                    "type": "string",
                    "required": True,
                    "description": "CSS选择器或XPath"
                },
                "text": {
                    "type": "string",
                    "required": True,
                    "description": "期望的文本内容"
                },
                "match_type": {
                    "type": "string",
                    "enum": ["contains", "exact", "regex"],
                    "default": "contains",
                    "description": "匹配模式"
                }
            },
            "enabled": True
        },
        {
            "name": "ASSERT_URL",
            "keyword_type": "builtin",
            "category": "ui",
            "description": "断言当前页面URL",
            "parameter_schema": {
                "url": {
                    "type": "string",
                    "required": True,
                    "description": "期望的URL"
                },
                "match_type": {
                    "type": "string",
                    "enum": ["contains", "exact"],
                    "default": "contains",
                    "description": "匹配模式"
                }
            },
            "enabled": True
        },
        {
            "name": "ASSERT_TITLE",
            "keyword_type": "builtin",
            "category": "ui",
            "description": "断言页面标题",
            "parameter_schema": {
                "title": {
                    "type": "string",
                    "required": True,
                    "description": "期望的页面标题"
                },
                "match_type": {
                    "type": "string",
                    "enum": ["contains", "exact"],
                    "default": "contains",
                    "description": "匹配模式"
                }
            },
            "enabled": True
        },
        {
            "name": "GET_TEXT",
            "keyword_type": "builtin",
            "category": "ui",
            "description": "获取元素的文本内容",
            "parameter_schema": {
                "selector": {
                    "type": "string",
                    "required": True,
                    "description": "CSS选择器或XPath"
                }
            },
            "enabled": True
        },
        {
            "name": "SELECT",
            "keyword_type": "builtin",
            "category": "ui",
            "description": "选择下拉框选项",
            "parameter_schema": {
                "selector": {
                    "type": "string",
                    "required": True,
                    "description": "下拉框选择器"
                },
                "value": {
                    "type": "string",
                    "required": True,
                    "description": "选项值（根据by参数解释）"
                },
                "by": {
                    "type": "string",
                    "enum": ["value", "label", "index"],
                    "default": "value",
                    "description": "选择方式：value=按值, label=按标签, index=按索引"
                },
                "timeout": {
                    "type": "integer",
                    "default": 5000,
                    "description": "超时时间（毫秒）"
                }
            },
            "enabled": True
        }
    ]

    try:
        print("=" * 60)
        print("数据库迁移: 添加 Phase 1 关键字")
        print("=" * 60)
        print()

        for keyword in keywords:
            # 检查关键字是否已存在
            cursor.execute(
                "SELECT id FROM keywords WHERE name = ? AND category = ?",
                (keyword["name"], keyword["category"])
            )
            existing = cursor.fetchone()

            if existing:
                print(f"⏭️  关键字 {keyword['name']} 已存在，跳过")
                continue

            # 生成 UUID（简化版，实际应使用 uuid 模块）
            import uuid
            keyword_id = str(uuid.uuid4()).replace('-', '')

            # 插入关键字
            cursor.execute("""
                INSERT INTO keywords (id, name, keyword_type, category, description, parameter_schema, is_valid)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                keyword_id,
                keyword["name"],
                keyword["keyword_type"],
                keyword["category"],
                keyword["description"],
                json.dumps(keyword["parameter_schema"]),
                1 if keyword["enabled"] else 0
            ))

            print(f"✓ 添加关键字: {keyword['name']}")

        conn.commit()
        print()
        print("=" * 60)
        print("✓ Phase 1 关键字迁移完成！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = add_phase1_keywords()

    if success:
        # 验证关键字已添加
        conn = sqlite3.connect('test_platform.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, category, description
            FROM keywords
            WHERE name IN ('ASSERT_VISIBLE', 'ASSERT_TEXT', 'ASSERT_URL',
                           'ASSERT_TITLE', 'GET_TEXT', 'SELECT')
            ORDER BY name
        """)

        print()
        print("已添加的关键字:")
        print("-" * 60)
        for row in cursor.fetchall():
            print(f"  {row[0]:<20} {row[1]:<10} {row[2]}")

        conn.close()
        sys.exit(0)
    else:
        sys.exit(1)
