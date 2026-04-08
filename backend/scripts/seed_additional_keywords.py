"""
补充 UI 关键字到数据库

将代码中已实现但数据库中缺失的关键字添加到数据库
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.keyword import Keyword
import uuid

# 定义缺失的关键字
MISSING_KEYWORDS = [
    {
        "name": "SCREENSHOT",
        "category": "ui",
        "description": "截取页面截图",
        "parameters": {
            "path": {"type": "string", "description": "截图保存路径", "required": False},
            "full_page": {"type": "boolean", "description": "是否全页截图", "default": False}
        },
        "enabled": True
    },
    {
        "name": "SELECT",
        "category": "ui",
        "description": "选择下拉框选项",
        "parameters": {
            "selector": {"type": "string", "description": "选择器", "required": True},
            "value": {"type": "string", "description": "选项值", "required": False},
            "text": {"type": "string", "description": "选项文本", "required": False},
            "timeout": {"type": "integer", "description": "超时时间（毫秒）", "default": 5000}
        },
        "enabled": True
    },
    {
        "name": "CHECKBOX",
        "category": "ui",
        "description": "勾选/取消勾选复选框",
        "parameters": {
            "selector": {"type": "string", "description": "选择器", "required": True},
            "checked": {"type": "boolean", "description": "是否勾选", "required": True},
            "timeout": {"type": "integer", "description": "超时时间（毫秒）", "default": 5000}
        },
        "enabled": True
    },
    {
        "name": "HOVER",
        "category": "ui",
        "description": "鼠标悬停",
        "parameters": {
            "selector": {"type": "string", "description": "选择器", "required": True},
            "timeout": {"type": "integer", "description": "超时时间（毫秒）", "default": 5000}
        },
        "enabled": True
    },
    {
        "name": "ASSERT_TEXT",
        "category": "assertion",
        "description": "断言文本存在",
        "parameters": {
            "text": {"type": "string", "description": "期望的文本", "required": True},
            "selector": {"type": "string", "description": "元素选择器（可选）", "required": False},
            "mode": {"type": "string", "description": "匹配模式: contains/equals", "default": "contains"},
            "timeout": {"type": "integer", "description": "超时时间（毫秒）", "default": 10000}
        },
        "enabled": True
    },
    {
        "name": "GET_TEXT",
        "category": "ui",
        "description": "提取元素文本或属性",
        "parameters": {
            "selector": {"type": "string", "description": "选择器", "required": True},
            "attribute": {"type": "string", "description": "属性名（可选，默认提取文本）", "required": False},
            "timeout": {"type": "integer", "description": "超时时间（毫秒）", "default": 5000}
        },
        "enabled": True
    },
    {
        "name": "SCROLL",
        "category": "ui",
        "description": "滚动页面",
        "parameters": {
            "direction": {"type": "string", "description": "滚动方向: up/down/left/right", "default": "down"},
            "pixels": {"type": "integer", "description": "滚动像素数", "default": 500},
            "selector": {"type": "string", "description": "元素选择器（可选，滚动到元素）", "required": False},
            "timeout": {"type": "integer", "description": "超时时间（毫秒）", "default": 5000}
        },
        "enabled": True
    }
]

def main():
    db = SessionLocal()

    try:
        # 添加每个缺失的关键字
        for kw_data in MISSINGING_KEYWORDS:
            # 检查是否已存在
            existing = db.query(Keyword).filter(Keyword.name == kw_data["name"]).first()

            if existing:
                print(f"⚠️  关键字 {kw_data['name']} 已存在，跳过")
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

        print(f"\n✅ 完成！共添加了 {len(MISSING_KEYWORDS)} 个关键字")

    except Exception as e:
        print(f"❌ 错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
