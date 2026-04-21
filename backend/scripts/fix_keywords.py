# backend/scripts/fix_keywords.py
"""
修复关键字类别 - 使用正确的英文类别
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.keyword import Keyword
from uuid import uuid4

def fix_keywords():
    """修复关键字类别"""
    db: Session = SessionLocal()
    try:
        # 删除所有现有的关键字
        print("🗑️  清除现有关键字...")
        db.query(Keyword).delete()
        db.commit()

        # 定义正确的关键字，使用正确的类别
        CORRECT_KEYWORDS = [
            # API 关键字
            {"name": "API_GET", "keyword_type": "system", "category": "api", "description": "发送 HTTP GET 请求", "parameter_schema": {"url": {"type": "string", "required": True}, "headers": {"type": "object", "required": False, "default": {}}, "params": {"type": "object", "required": False, "default": {}}}},
            {"name": "API_POST", "keyword_type": "system", "category": "api", "description": "发送 HTTP POST 请求", "parameter_schema": {"url": {"type": "string", "required": True}, "headers": {"type": "object", "required": False, "default": {}}, "body": {"type": "object", "required": True}}},

            # UI 基础操作
            {"name": "OPEN_BROWSER", "keyword_type": "system", "category": "ui", "description": "打开浏览器", "parameter_schema": {"browser": {"type": "string", "required": False, "default": "chromium"}, "headless": {"type": "boolean", "required": False, "default": True}}},
            {"name": "CLOSE_BROWSER", "keyword_type": "system", "category": "ui", "description": "关闭浏览器", "parameter_schema": {}},
            {"name": "NAVIGATE", "keyword_type": "system", "category": "ui", "description": "导航到指定 URL", "parameter_schema": {"url": {"type": "string", "required": True}}},
            {"name": "SWITCH_TAB", "keyword_type": "system", "category": "ui", "description": "切换浏览器标签页", "parameter_schema": {"index": {"type": "integer", "required": True}}},
            {"name": "GO_BACK", "keyword_type": "system", "category": "ui", "description": "浏览器后退", "parameter_schema": {}},
            {"name": "REFRESH", "keyword_type": "system", "category": "ui", "description": "刷新页面", "parameter_schema": {"force": {"type": "boolean", "required": False, "default": False}}},
            {"name": "SCREENSHOT", "keyword_type": "system", "category": "ui", "description": "截图保存", "parameter_schema": {"path": {"type": "string", "required": False}}},

            # 元素操作
            {"name": "CLICK", "keyword_type": "system", "category": "ui", "description": "点击页面元素", "parameter_schema": {"selector": {"type": "string", "required": True}, "timeout": {"type": "integer", "required": False, "default": 30000}}},
            {"name": "DOUBLE_CLICK", "keyword_type": "system", "category": "ui", "description": "双击页面元素", "parameter_schema": {"selector": {"type": "string", "required": True}, "timeout": {"type": "integer", "required": False, "default": 30000}}},
            {"name": "INPUT", "keyword_type": "system", "category": "ui", "description": "在输入框中输入文本", "parameter_schema": {"selector": {"type": "string", "required": True}, "text": {"type": "string", "required": True}, "timeout": {"type": "integer", "required": False, "default": 30000}}},
            {"name": "HOVER", "keyword_type": "system", "category": "ui", "description": "鼠标悬停在元素上", "parameter_schema": {"selector": {"type": "string", "required": True}, "timeout": {"type": "integer", "required": False, "default": 30000}}},
            {"name": "RIGHT_CLICK", "keyword_type": "system", "category": "ui", "description": "右键点击元素", "parameter_schema": {"selector": {"type": "string", "required": True}, "timeout": {"type": "integer", "required": False, "default": 30000}}},
            {"name": "SELECT_OPTION", "keyword_type": "system", "category": "ui", "description": "在下拉框中选择选项", "parameter_schema": {"selector": {"type": "string", "required": True}, "value": {"type": "string", "required": True}, "timeout": {"type": "integer", "required": False, "default": 30000}}},
            {"name": "UPLOAD_FILE", "keyword_type": "system", "category": "ui", "description": "上传文件", "parameter_schema": {"selector": {"type": "string", "required": True}, "file_path": {"type": "string", "required": True}}},

            # 断言操作
            {"name": "ASSERT_STATUS", "keyword_type": "system", "category": "assertion", "description": "断言 HTTP 状态码", "parameter_schema": {"expected_status": {"type": "integer", "required": True}}},
            {"name": "ASSERT_VISIBLE", "keyword_type": "system", "category": "assertion", "description": "断言元素可见", "parameter_schema": {"selector": {"type": "string", "required": True}, "timeout": {"type": "integer", "required": False, "default": 5000}}},
            {"name": "ASSERT_TEXT", "keyword_type": "system", "category": "assertion", "description": "断言元素文本内容", "parameter_schema": {"selector": {"type": "string", "required": True}, "expected": {"type": "string", "required": True}, "timeout": {"type": "integer", "required": False, "default": 5000}}},

            # 等待操作
            {"name": "WAIT_FOR_ELEMENT", "keyword_type": "system", "category": "ui", "description": "等待元素出现", "parameter_schema": {"selector": {"type": "string", "required": True}, "state": {"type": "string", "required": False, "default": "visible"}, "timeout": {"type": "integer", "required": False, "default": 30000}}},

            # 数据提取
            {"name": "EXTRACT_VARIABLE", "keyword_type": "system", "category": "extract", "description": "从响应中提取变量", "parameter_schema": {"variable_name": {"type": "string", "required": True}, "extract_from": {"type": "string", "required": True}, "extract_type": {"type": "string", "required": True}, "expression": {"type": "string", "required": True}}},
            {"name": "GET_TEXT", "keyword_type": "system", "category": "data", "description": "获取元素文本内容", "parameter_schema": {"selector": {"type": "string", "required": True}, "timeout": {"type": "integer", "required": False, "default": 30000}}},
            {"name": "GET_ATTRIBUTE", "keyword_type": "system", "category": "data", "description": "获取元素属性值", "parameter_schema": {"selector": {"type": "string", "required": True}, "attribute": {"type": "string", "required": True}, "timeout": {"type": "integer", "required": False, "default": 30000}}},
        ]

        print(f"📝 添加 {len(CORRECT_KEYWORDS)} 个关键字...")
        for kw_data in CORRECT_KEYWORDS:
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
            print(f"✅ 添加关键字: {kw_data['name']} ({kw_data['category']})")

        db.commit()
        print(f"\n🎉 成功创建 {len(CORRECT_KEYWORDS)} 个关键字")

        # 按类别显示统计
        keywords = db.query(Keyword).all()
        category_count = {}
        for kw in keywords:
            category_count[kw.category] = category_count.get(kw.category, 0) + 1

        print("\n📊 关键字分类统计:")
        for category, count in sorted(category_count.items()):
            print(f"   {category}: {count} 个")

    except Exception as e:
        db.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("修复关键字类别 - 使用正确的英文类别")
    print("=" * 60)
    fix_keywords()