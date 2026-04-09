"""
数据库迁移：添加 debug_info 字段

为 step_executions 表添加 debug_info 字段，用于存储调试信息
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import Settings

def migrate():
    """执行迁移"""
    print("开始迁移: 添加 debug_info 字段...")

    # 获取数据库 URL
    settings = Settings()
    db_url = settings.DATABASE_URL or "sqlite:///./test_platform.db"

    print(f"使用数据库: {db_url}")

    # 创建数据库引擎
    engine = create_engine(db_url)

    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("PRAGMA table_info(step_executions)"))
        columns = result.fetchall()
        column_names = [col[1] for col in columns]

        if "debug_info" in column_names:
            print("⚠️  debug_info 字段已存在，跳过迁移")
            return

        # 添加 debug_info 字段
        try:
            conn.execute(text("ALTER TABLE step_executions ADD COLUMN debug_info TEXT"))
            conn.commit()
            print("✅ 成功添加 debug_info 字段到 step_executions 表")
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            conn.rollback()
            raise

    # 验证迁移结果
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(step_executions)"))
        columns = result.fetchall()

        print("\nstep_executions 表字段:")
        for col in columns:
            print(f"  - {col[1]:20} {col[2]:15}")

    print("\n✅ 迁移完成")

if __name__ == "__main__":
    migrate()
