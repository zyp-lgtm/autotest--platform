# backend/scripts/seed_keywords.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.keyword import Keyword
import json

SYSTEM_KEYWORDS = [
    # API 关键字
    {
        "name": "API_GET",
        "keyword_type": "system",
        "category": "api",
        "description": "发送 HTTP GET 请求",
        "icon": "📡",
        "parameter_schema": {
            "url": {"type": "string", "required": True, "description": "请求 URL"},
            "headers": {"type": "object", "required": False, "default": {}},
            "params": {"type": "object", "required": False, "default": {}}
        },
        "return_schema": {
            "status_code": "整数",
            "headers": "对象",
            "body": "对象"
        }
    },
    {
        "name": "API_POST",
        "keyword_type": "system",
        "category": "api",
        "description": "发送 HTTP POST 请求",
        "icon": "📤",
        "parameter_schema": {
            "url": {"type": "string", "required": True},
            "headers": {"type": "object", "required": False, "default": {}},
            "body": {"type": "object", "required": True}
        },
        "return_schema": {
            "status_code": "整数",
            "headers": "对象",
            "body": "对象"
        }
    },
    {
        "name": "ASSERT_STATUS",
        "keyword_type": "system",
        "category": "assertion",
        "description": "断言 HTTP 状态码",
        "icon": "✅",
        "parameter_schema": {
            "expected_status": {"type": "integer", "required": True}
        },
        "return_schema": {
            "passed": "布尔值",
            "expected": "整数",
            "actual": "整数"
        }
    },
    {
        "name": "EXTRACT_VARIABLE",
        "keyword_type": "system",
        "category": "extract",
        "description": "从响应中提取变量",
        "icon": "📥",
        "parameter_schema": {
            "variable_name": {"type": "string", "required": True},
            "extract_from": {"type": "string", "required": True},
            "extract_type": {"type": "string", "required": True},
            "expression": {"type": "string", "required": True}
        },
        "return_schema": {
            "success": "布尔值"
        }
    },
    # UI 关键字
    {
        "name": "NAVIGATE",
        "keyword_type": "system",
        "category": "ui",
        "description": "导航到指定 URL",
        "icon": "🌐",
        "parameter_schema": {
            "url": {"type": "string", "required": True}
        },
        "return_schema": {
            "success": "布尔值"
        }
    },
    {
        "name": "CLICK",
        "keyword_type": "system",
        "category": "ui",
        "description": "点击页面元素",
        "icon": "👆",
        "parameter_schema": {
            "selector": {"type": "string", "required": True},
            "timeout": {"type": "integer", "required": False, "default": 30000}
        },
        "return_schema": {
            "success": "布尔值"
        }
    },
    {
        "name": "INPUT",
        "keyword_type": "system",
        "category": "ui",
        "description": "在输入框中输入文本",
        "icon": "⌨️",
        "parameter_schema": {
            "selector": {"type": "string", "required": True},
            "text": {"type": "string", "required": True},
            "clear_first": {"type": "boolean", "required": False, "default": True}
        },
        "return_schema": {
            "success": "布尔值"
        }
    },
    {
        "name": "WAIT_FOR_ELEMENT",
        "keyword_type": "system",
        "category": "ui",
        "description": "等待元素出现",
        "icon": "⏳",
        "parameter_schema": {
            "selector": {"type": "string", "required": True},
            "state": {"type": "string", "required": False, "default": "visible"},
            "timeout": {"type": "integer", "required": False, "default": 30000}
        },
        "return_schema": {
            "success": "布尔值"
        }
    },
]


def seed_keywords():
    db: Session = SessionLocal()

    try:
        # 创建表
        Base.metadata.create_all(bind=engine)

        # 检查关键字是否已存在
        existing = db.query(Keyword).filter_by(name="API_GET").first()
        if existing:
            print("关键字已存在，跳过种子")
            return

        # 种植关键字
        for kw_data in SYSTEM_KEYWORDS:
            keyword = Keyword(**kw_data)
            db.add(keyword)

        db.commit()
        print(f"成功种植 {len(SYSTEM_KEYWORDS)} 个系统关键字")

    except Exception as e:
        print(f"种植关键字时出错: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_keywords()