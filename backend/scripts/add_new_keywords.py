"""
添加新增的 UI 关键字到数据库
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.keyword import Keyword
import logging

logger = logging.getLogger(__name__)

# 新增关键字定义
NEW_KEYWORDS = [
    {
        "name": "CLOSE_BROWSER",
        "category": "ui",
        "keyword_type": "action",
        "description": "关闭浏览器（清理测试环境）",
        "parameter_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "SWITCH_TAB",
        "category": "ui",
        "keyword_type": "action",
        "description": "切换到指定的浏览器标签页",
        "parameter_schema": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": "标签页索引（从0开始），默认为1",
                    "default": 1
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（毫秒），默认为5000",
                    "default": 5000
                }
            },
            "required": []
        }
    },
    {
        "name": "GO_BACK",
        "category": "ui",
        "keyword_type": "action",
        "description": "在浏览器历史记录中后退一页",
        "parameter_schema": {
            "type": "object",
            "properties": {
                "wait_until": {
                    "type": "string",
                    "description": "等待条件：load/domcontentloaded/networkidle",
                    "enum": ["load", "domcontentloaded", "networkidle"],
                    "default": "load"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（毫秒），默认为30000",
                    "default": 30000
                }
            },
            "required": []
        }
    },
    {
        "name": "REFRESH",
        "category": "ui",
        "keyword_type": "action",
        "description": "刷新当前页面",
        "parameter_schema": {
            "type": "object",
            "properties": {
                "wait_until": {
                    "type": "string",
                    "description": "等待条件：load/domcontentloaded/networkidle",
                    "enum": ["load", "domcontentloaded", "networkidle"],
                    "default": "load"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（毫秒），默认为30000",
                    "default": 30000
                }
            },
            "required": []
        }
    },
    {
        "name": "DOUBLE_CLICK",
        "category": "ui",
        "keyword_type": "action",
        "description": "双击指定元素",
        "parameter_schema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS选择器"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（毫秒），默认为5000",
                    "default": 5000
                },
                "force": {
                    "type": "boolean",
                    "description": "是否强制点击（忽略可见性），默认为False",
                    "default": False
                }
            },
            "required": ["selector"]
        }
    }
]


def add_keywords():
    """添加新关键字到数据库"""
    with Session(engine) as db:
        added_count = 0
        skipped_count = 0

        for keyword_def in NEW_KEYWORDS:
            # 检查关键字是否已存在
            existing = db.query(Keyword).filter(
                Keyword.name == keyword_def["name"],
                Keyword.category == keyword_def["category"]
            ).first()

            if existing:
                logger.info(f"⊙ 关键字已存在，跳过: {keyword_def['name']}")
                skipped_count += 1
                continue

            # 创建新关键字
            keyword = Keyword(
                name=keyword_def["name"],
                category=keyword_def["category"],
                keyword_type=keyword_def.get("keyword_type", "action"),
                description=keyword_def["description"],
                parameter_schema=keyword_def["parameter_schema"]
            )

            db.add(keyword)
            added_count += 1
            logger.info(f"✓ 添加关键字: {keyword_def['name']}")

        # 提交更改
        if added_count > 0:
            db.commit()
            logger.info(f"✅ 成功添加 {added_count} 个新关键字")

        if skipped_count > 0:
            logger.info(f"ℹ️  跳过 {skipped_count} 个已存在的关键字")


def list_ui_keywords():
    """列出所有 UI 关键字"""
    with Session(engine) as db:
        ui_keywords = db.query(Keyword).filter(
            Keyword.category == "ui"
        ).order_by(Keyword.name).all()

        print("\n当前 UI 关键字列表:")
        print("=" * 80)
        print(f"{'关键字名称':<20} {'描述':<40}")
        print("=" * 80)

        for kw in ui_keywords:
            print(f"{kw.name:<20} {kw.description:<40}")

        print("=" * 80)
        print(f"总计: {len(ui_keywords)} 个 UI 关键字")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    print("=" * 80)
    print("添加新增的 UI 关键字")
    print("=" * 80)
    print()

    try:
        add_keywords()
        print()
        list_ui_keywords()
        print()
        print("=" * 80)
        print("✅ 完成！")
        print("=" * 80)

    except Exception as e:
        logger.error(f"❌ 添加关键字失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
