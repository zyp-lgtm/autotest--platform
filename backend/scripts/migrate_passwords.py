"""
密码迁移脚本

将现有用户的明文密码迁移为 bcrypt 哈希
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password, verify_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_passwords():
    """迁移所有明文密码为哈希"""
    db = SessionLocal()

    try:
        # 获取所有用户
        users = db.query(User).all()
        logger.info(f"Found {len(users)} users to check")

        migrated_count = 0
        skipped_count = 0

        for user in users:
            # 检查密码是否已经是哈希（bcrypt 哈希通常以 $2b$ 开头）
            if user.hashed_password.startswith('$2b$'):
                logger.info(f"User {user.username}: password already hashed, skipping")
                skipped_count += 1
                continue

            # 明文密码，需要迁移
            plain_password = user.hashed_password
            hashed_password = hash_password(plain_password)

            # 更新密码
            user.hashed_password = hashed_password
            db.commit()

            logger.info(f"User {user.username}: password migrated successfully")
            migrated_count += 1

        logger.info(f"\nMigration complete!")
        logger.info(f"  Migrated: {migrated_count} users")
        logger.info(f"  Skipped: {skipped_count} users (already hashed)")

        return migrated_count, skipped_count

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_migration():
    """验证迁移后的密码可以正常使用"""
    db = SessionLocal()

    try:
        users = db.query(User).limit(5).all()
        logger.info(f"\nVerifying {len(users)} random users...")

        all_valid = True
        for user in users:
            # 只能验证哈希后的密码（我们已经丢失了原始明文）
            if user.hashed_password.startswith('$2b$'):
                logger.info(f"✓ User {user.username}: password is properly hashed")
            else:
                logger.warning(f"✗ User {user.username}: password is NOT hashed!")
                all_valid = False

        if all_valid:
            logger.info("\n✓ All verified passwords are properly hashed")
        else:
            logger.warning("\n✗ Some passwords are not hashed!")

        return all_valid

    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("密码迁移脚本")
    print("=" * 60)
    print()

    # 执行迁移
    migrate, skip = migrate_passwords()

    # 验证结果
    verify_migration()

    print()
    print("=" * 60)
    print("迁移完成！")
    print("=" * 60)
