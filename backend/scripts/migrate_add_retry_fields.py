"""
添加重试相关字段到 step_executions 表
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
    """添加重试相关字段"""
    try:
        with engine.connect() as conn:
            # 检查字段是否已存在
            result = conn.execute(
                text("PRAGMA table_info(step_executions)")
            ).fetchall()

            column_names = [row[1] for row in result]

            # 添加 retry_attempt 字段
            if 'retry_attempt' not in column_names:
                conn.execute(
                    text("ALTER TABLE step_executions ADD COLUMN retry_attempt INTEGER DEFAULT 0")
                )
                conn.commit()
                logger.info("✓ 成功添加 retry_attempt 字段")
            else:
                logger.info("retry_attempt 字段已存在，跳过")

            # 添加 retry_of 字段
            if 'retry_of' not in column_names:
                conn.execute(
                    text("ALTER TABLE step_executions ADD COLUMN retry_of UUID")
                )
                conn.commit()
                logger.info("✓ 成功添加 retry_of 字段")
            else:
                logger.info("retry_of 字段已存在，跳过")

    except Exception as e:
        logger.error(f"迁移失败: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate()
    logger.info("迁移完成")
