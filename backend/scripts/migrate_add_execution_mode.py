"""
添加 execution_mode 字段到 test_executions 表
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import engine
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def migrate():
    """添加 execution_mode 字段"""
    try:
        with engine.connect() as conn:
            # 检查字段是否已存在
            result = conn.execute(
                text("PRAGMA table_info(test_executions)")
            ).fetchall()

            column_names = [row[1] for row in result]

            if 'execution_mode' in column_names:
                logger.info("execution_mode 字段已存在，跳过迁移")
                return

            # 添加字段
            conn.execute(
                text("ALTER TABLE test_executions ADD COLUMN execution_mode VARCHAR(20) DEFAULT 'direct'")
            )
            conn.commit()
            logger.info("✓ 成功添加 execution_mode 字段到 test_executions 表")

            # 更新现有记录
            conn.execute(
                text("UPDATE test_executions SET execution_mode = 'direct' WHERE execution_mode IS NULL")
            )
            conn.commit()
            logger.info("✓ 已更新现有记录的 execution_mode 为 'direct'")

    except Exception as e:
        logger.error(f"迁移失败: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate()
    logger.info("迁移完成")
