# backend/scripts/add_additional_keywords.py
"""
添加额外的UI关键字到数据库
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.keyword import Keyword
from uuid import uuid4
import json

ADDITIONAL_KEYWORDS = [
    {
        "name": "OPEN_BROWSER",
        "keyword_type": "system",
        "category": "浏览器控制",
        "description": "打开浏览器",
        "parameter_schema": {
            "browser": {"type": "string", "required": False, "default": "chromium", "description": "浏览器类型: chromium, firefox, webkit"},
            "headless": {"type": "boolean", "required": False, "default": True, "description": "是否无头模式"}
        }
    },
    {
        "name": "CLOSE_BROWSER",
        "keyword_type": "system",
        "category": "浏览器控制",
        "description": "关闭浏览器",
        "parameter_schema": {}
    },
    {
        "name": "SWITCH_TAB",
        "keyword_type": "system",
        "category": "浏览器控制",
        "description": "切换浏览器标签页",
        "parameter_schema": {
            "index": {"type": "integer", "required": True, "description": "标签页索引，从0开始"}
        }
    },
    {
        "name": "GO_BACK",
        "keyword_type": "system",
        "category": "浏览器控制",
        "description": "浏览器后退",
        "parameter_schema": {}
    },
    {
        "name": "REFRESH",
        "keyword_type": "system",
        "category": "浏览器控制",
        "description": "刷新页面",
        "parameter_schema": {
            "force": {"type": "boolean", "required": False, "default": False, "description": "是否强制刷新"}
        }
    },
    {
        "name": "DOUBLE_CLICK",
        "keyword_type": "system",
        "category": "元素操作",
        "description": "双击页面元素",
        "parameter_schema": {
            "selector": {"type": "string", "required": True, "description": "CSS选择器"},
            "timeout": {"type": "integer", "required": False, "default": 30000, "description": "超时时间(毫秒)"}
        }
    },
    {
        "name": "ASSERT_VISIBLE",
        "keyword_type": "system",
        "category": "断言操作",
        "description": "断言元素可见",
        "parameter_schema": {
            "selector": {"type": "string", "required": True, "description": "CSS选择器"},
            "timeout": {"type": "integer", "required": False, "default": 5000, "description": "超时时间(毫秒)"}
        }
    },
    {
        "name": "ASSERT_TEXT",
        "keyword_type": "system",
        "category": "断言操作",
        "description": "断言元素文本内容",
        "parameter_schema": {
            "selector": {"type": "string", "required": True, "description": "CSS选择器"},
            "expected": {"type": "string", "required": True, "description": "期望的文本内容"},
            "timeout": {"type": "integer", "required": False, "default": 5000, "description": "超时时间(毫秒)"}
        }
    },
    {
        "name": "WAIT_FOR_ELEMENT",
        "keyword_type": "system",
        "category": "等待操作",
        "description": "等待元素出现",
        "parameter_schema": {
            "selector": {"type": "string", "required": True, "description": "CSS选择器"},
            "state": {"type": "string", "required": False, "default": "visible", "description": "元素状态: visible, attached, hidden"},
            "timeout": {"type": "integer", "required": False, "default": 30000, "description": "超时时间(毫秒)"}
        }
    },
    {
        "name": "HOVER",
        "keyword_type": "system",
        "category": "元素操作",
        "description": "鼠标悬停在元素上",
        "parameter_schema": {
            "selector": {"type": "string", "required": True, "description": "CSS选择器"},
            "timeout": {"type": "integer", "required": False, "default": 30000, "description": "超时时间(毫秒)"}
        }
    },
    {
        "name": "RIGHT_CLICK",
        "keyword_type": "system",
        "category": "元素操作",
        "description": "右键点击元素",
        "parameter_schema": {
            "selector": {"type": "string", "required": True, "description": "CSS选择器"},
            "timeout": {"type": "integer", "required": False, "default": 30000, "description": "超时时间(毫秒)"}
        }
    },
    {
        "name": "SELECT_OPTION",
        "keyword_type": "system",
        "category": "元素操作",
        "description": "在下拉框中选择选项",
        "parameter_schema": {
            "selector": {"type": "string", "required": True, "description": "CSS选择器"},
            "value": {"type": "string", "required": True, "description": "要选择的选项值"},
            "timeout": {"type": "integer", "required": False, "default": 30000, "description": "超时时间(毫秒)"}
        }
    },
    {
        "name": "GET_TEXT",
        "keyword_type": "system",
        "category": "数据提取",
        "description": "获取元素文本内容",
        "parameter_schema": {
            "selector": {"type": "string", "required": True, "description": "CSS选择器"},
            "timeout": {"type": "integer", "required": False, "default": 30000, "description": "超时时间(毫秒)"}
        }
    },
    {
        "name": "GET_ATTRIBUTE",
        "keyword_type": "system",
        "category": "数据提取",
        "description": "获取元素属性值",
        "parameter_schema": {
            "selector": {"type": "string", "required": True, "description": "CSS选择器"},
            "attribute": {"type": "string", "required": True, "description": "属性名称"},
            "timeout": {"type": "integer", "required": False, "default": 30000, "description": "超时时间(毫秒)"}
        }
    },
    {
        "name": "SCREENSHOT",
        "keyword_type": "system",
        "category": "浏览器控制",
        "description": "截图保存",
        "parameter_schema": {
            "path": {"type": "string", "required": False, "description": "保存路径，不指定则自动生成"}
        }
    },
    {
        "name": "UPLOAD_FILE",
        "keyword_type": "system",
        "category": "元素操作",
        "description": "上传文件",
        "parameter_schema": {
            "selector": {"type": "string", "required": True, "description": "CSS选择器"},
            "file_path": {"type": "string", "required": True, "description": "文件路径"}
        }
    }
]

def add_keywords():
    """添加额外关键字到数据库"""
    db: Session = SessionLocal()
    try:
        added_count = 0
        skipped_count = 0

        for kw_data in ADDITIONAL_KEYWORDS:
            # 检查是否已存在
            existing = db.query(Keyword).filter_by(name=kw_data["name"]).first()
            if existing:
                print(f"⏭️  跳过已存在的关键字: {kw_data['name']}")
                skipped_count += 1
                continue

            # 创建新关键字
            keyword = Keyword(
                id=uuid4(),
                name=kw_data["name"],
                keyword_type=kw_data["keyword_type"],
                category=kw_data["category"],
                description=kw_data["description"],
                parameter_schema=kw_data["parameter_schema"],
                is_valid=True
            )

            db.add(keyword)
            added_count += 1
            print(f"✅ 添加关键字: {kw_data['name']} ({kw_data['category']})")

        db.commit()
        print(f"\n📊 统计: 新增 {added_count} 个，跳过 {skipped_count} 个")

        # 显示总数
        total = db.query(Keyword).count()
        print(f"🎉 数据库中现在共有 {total} 个关键字")

    except Exception as e:
        db.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("添加额外的UI关键字")
    print("=" * 60)
    add_keywords()