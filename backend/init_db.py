#!/usr/bin/env python3
"""
初始化数据库和创建测试用户
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.user import User
from app.core.security import hash_password

settings = get_settings()

# 创建数据库引擎
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """初始化数据库表"""
    from app.core.database import Base
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表创建完成")

def create_test_user():
    """创建测试用户"""
    db = SessionLocal()
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == "demo").first()
        if existing_user:
            print("✓ 测试用户已存在")
            return

        # 创建测试用户
        test_user = User(
            username="demo",
            email="demo@example.com",
            full_name="演示用户",
            hashed_password=hash_password("demo123")
        )

        db.add(test_user)
        db.commit()

        print("✓ 测试用户创建成功")
        print("  用户名: demo")
        print("  密码: demo123")
        print("  邮箱: demo@example.com")

    except Exception as e:
        print(f"✗ 创建测试用户失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("数据库初始化")
    print("=" * 60)
    print(f"数据库: {settings.DATABASE_URL}")
    print()

    try:
        init_database()
        print()
        create_test_user()
        print()
        print("=" * 60)
        print("初始化完成！")
        print("=" * 60)
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        sys.exit(1)
