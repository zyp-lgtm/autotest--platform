"""
数据库初始化脚本

创建所有数据库表并添加初始数据
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, engine, SessionLocal
from app.models import user, project, keyword, test_data, ui_task, api_task, execution

def init_db():
    """初始化数据库"""
    print("开始初始化数据库...")

    # 创建所有表
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功")

    # 显示所有表
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("\n当前数据库表:")
    for table in sorted(tables):
        print(f"  - {table}")

    print("\n✅ 数据库初始化完成")

if __name__ == "__main__":
    init_db()
