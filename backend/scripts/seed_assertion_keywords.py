"""
添加断言关键字到数据库

新增的断言关键字:
- ASSERT_VISIBLE - 断言元素可见
- ASSERT_URL - 断言 URL
- ASSERT_TITLE - 断言标题
- ASSERT_ELEMENT_COUNT - 断言元素数量
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.keyword import Keyword
import uuid

# 定义新增的断言关键字
ASSERTION_KEYWORDS = [
    {
        "name": "ASSERT_VISIBLE",
        "keyword_type": "assertion",
        "category": "assertion",
        "description": "断言元素可见或不可见",
        "parameter_schema": {
            "selector": {
                "type": "string",
                "description": "元素选择器",
                "required": True
            },
            "visible": {
                "type": "boolean",
                "description": "True=断言可见, False=断言不可见",
                "default": True
            },
            "timeout": {
                "type": "integer",
                "description": "超时时间（毫秒）",
                "default": 10000
            }
        }
    },
    {
        "name": "ASSERT_URL",
        "keyword_type": "assertion",
        "category": "assertion",
        "description": "断言当前 URL",
        "parameter_schema": {
            "url": {
                "type": "string",
                "description": "期望的 URL",
                "required": True
            },
            "mode": {
                "type": "string",
                "description": "匹配模式: contains/equals/regex",
                "default": "contains",
                "enum": ["contains", "equals", "regex"]
            },
            "timeout": {
                "type": "integer",
                "description": "超时时间（毫秒）",
                "default": 10000
            }
        }
    },
    {
        "name": "ASSERT_TITLE",
        "keyword_type": "assertion",
        "category": "assertion",
        "description": "断言页面标题",
        "parameter_schema": {
            "title": {
                "type": "string",
                "description": "期望的标题",
                "required": True
            },
            "mode": {
                "type": "string",
                "description": "匹配模式: contains/equals/regex",
                "default": "contains",
                "enum": ["contains", "equals", "regex"]
            },
            "timeout": {
                "type": "integer",
                "description": "超时时间（毫秒）",
                "default": 10000
            }
        }
    },
    {
        "name": "ASSERT_ELEMENT_COUNT",
        "keyword_type": "assertion",
        "category": "assertion",
        "description": "断言元素数量",
        "parameter_schema": {
            "selector": {
                "type": "string",
                "description": "元素选择器",
                "required": True
            },
            "operator": {
                "type": "string",
                "description": "比较符",
                "default": "==",
                "enum": ["==", "!=", ">", "<", ">=", "<="]
            },
            "count": {
                "type": "integer",
                "description": "期望的数量",
                "required": True
            },
            "timeout": {
                "type": "integer",
                "description": "超时时间（毫秒）",
                "default": 10000
            }
        }
    }
]

def main():
    db = SessionLocal()

    try:
        added_count = 0
        skipped_count = 0

        for kw_data in ASSERTION_KEYWORDS:
            # 检查是否已存在
            existing = db.query(Keyword).filter(Keyword.name == kw_data["name"]).first()

            if existing:
                print(f"⚠️  关键字 {kw_data['name']} 已存在，跳过")
                skipped_count += 1
                continue

            # 创建新关键字
            keyword = Keyword(
                id=uuid.uuid4(),
                **kw_data
            )

            db.add(keyword)
            db.commit()
            db.refresh(keyword)

            print(f"✅ 已添加关键字: {keyword.name} ({keyword.category})")
            added_count += 1

        print(f"\n✅ 完成！")
        print(f"  - 新增: {added_count} 个")
        print(f"  - 跳过: {skipped_count} 个")

    except Exception as e:
        print(f"❌ 错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
