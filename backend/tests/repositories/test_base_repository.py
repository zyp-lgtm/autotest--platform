"""
基础 Repository 测试

测试 BaseRepository 的通用 CRUD 操作
"""
import pytest
import uuid
from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository
from app.models.user import User


class TestBaseRepository:
    """测试 BaseRepository 基础功能"""

    def test_create_entity(self, session):
        """测试创建实体"""
        repo = BaseRepository(session, User)

        user = repo.create(
            username="newuser",
            email="newuser@example.com",
            hashed_password="hash",
            full_name="New User",
            is_active=True
        )

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"

    def test_get_by_id(self, session, test_user):
        """测试根据 ID 获取实体"""
        repo = BaseRepository(session, User)

        user = repo.get_by_id(str(test_user.id))

        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username

    def test_get_by_id_not_found(self, session):
        """测试获取不存在的实体"""
        repo = BaseRepository(session, User)

        user = repo.get_by_id(str(uuid.uuid4()))

        assert user is None

    def test_get_by_id_invalid_format(self, session):
        """测试无效的 ID 格式"""
        repo = BaseRepository(session, User)

        user = repo.get_by_id("invalid-uuid")

        assert user is None

    def test_get_by_id_or_raise_success(self, session, test_user):
        """测试成功获取实体"""
        repo = BaseRepository(session, User)

        user = repo.get_by_id_or_raise(str(test_user.id), "用户")

        assert user is not None
        assert user.id == test_user.id

    def test_get_by_id_or_raise_not_found(self, session):
        """测试获取不存在的实体抛出异常"""
        repo = BaseRepository(session, User)

        with pytest.raises(ValueError, match="用户不存在"):
            repo.get_by_id_or_raise(str(uuid.uuid4()), "用户")

    def test_get_by_id_or_raise_invalid_format(self, session):
        """测试无效 ID 格式抛出异常"""
        repo = BaseRepository(session, User)

        with pytest.raises(ValueError, match="无效的用户ID格式"):
            repo.get_by_id_or_raise("invalid-uuid", "用户")

    def test_list_all(self, session):
        """测试获取所有实体"""
        repo = BaseRepository(session, User)

        # 创建多个用户
        for i in range(3):
            repo.create(
                username=f"user{i}",
                email=f"user{i}@example.com",
                hashed_password="hash",
                is_active=True
            )

        users = repo.list_all()

        assert len(users) >= 3

    def test_list_all_with_limit(self, session):
        """测试限制返回数量"""
        repo = BaseRepository(session, User)

        # 创建多个用户
        for i in range(5):
            repo.create(
                username=f"user{i}",
                email=f"user{i}@example.com",
                hashed_password="hash",
                is_active=True
            )

        users = repo.list_all(limit=3)

        assert len(users) == 3

    def test_filter(self, session):
        """测试过滤实体"""
        repo = BaseRepository(session, User)

        # 创建不同状态的用户
        repo.create(username="active1", email="active1@example.com", hashed_password="hash", is_active=True)
        repo.create(username="inactive1", email="inactive1@example.com", hashed_password="hash", is_active=False)

        active_users = repo.filter(is_active=True)

        assert all(u.is_active for u in active_users)

    def test_filter_one(self, session):
        """测试过滤单个实体"""
        repo = BaseRepository(session, User)

        repo.create(username="unique", email="unique@example.com", hashed_password="hash", is_active=True)

        user = repo.filter_one(username="unique")

        assert user is not None
        assert user.username == "unique"

    def test_update(self, session, test_user):
        """测试更新实体"""
        repo = BaseRepository(session, User)

        updated_user = repo.update(str(test_user.id), full_name="Updated Name")

        assert updated_user is not None
        assert updated_user.full_name == "Updated Name"

    def test_update_not_found(self, session):
        """测试更新不存在的实体"""
        repo = BaseRepository(session, User)

        result = repo.update(str(uuid.uuid4()), full_name="Updated")

        assert result is None

    def test_delete(self, session, test_user):
        """测试删除实体"""
        repo = BaseRepository(session, User)

        success = repo.delete(str(test_user.id))

        assert success is True

        # 验证已删除
        deleted_user = repo.get_by_id(str(test_user.id))
        assert deleted_user is None

    def test_delete_not_found(self, session):
        """测试删除不存在的实体"""
        repo = BaseRepository(session, User)

        success = repo.delete(str(uuid.uuid4()))

        assert success is False

    def test_count(self, session):
        """测试统计实体数量"""
        repo = BaseRepository(session, User)

        # 创建用户
        for i in range(3):
            repo.create(
                username=f"user{i}",
                email=f"user{i}@example.com",
                hashed_password="hash",
                is_active=True
            )

        count = repo.count()

        assert count >= 3

    def test_count_with_filter(self, session):
        """测试带条件的统计"""
        repo = BaseRepository(session, User)

        repo.create(username="active1", email="active1@example.com", hashed_password="hash", is_active=True)
        repo.create(username="active2", email="active2@example.com", hashed_password="hash", is_active=True)
        repo.create(username="inactive1", email="inactive1@example.com", hashed_password="hash", is_active=False)

        active_count = repo.count(is_active=True)

        assert active_count == 2

    def test_exists(self, session):
        """测试检查实体是否存在"""
        repo = BaseRepository(session, User)

        repo.create(username="exists", email="exists@example.com", hashed_password="hash", is_active=True)

        assert repo.exists(username="exists") is True
        assert repo.exists(username="notexists") is False

    def test_bulk_create(self, session):
        """测试批量创建"""
        repo = BaseRepository(session, User)

        users_data = [
            {"username": f"user{i}", "email": f"user{i}@example.com", "hashed_password": "hash", "is_active": True}
            for i in range(3)
        ]

        users = repo.bulk_create(users_data)

        assert len(users) == 3
        assert all(u.id is not None for u in users)

    def test_get_in(self, session):
        """测试根据字段值列表获取实体"""
        repo = BaseRepository(session, User)

        # 创建用户
        usernames = ["user1", "user2", "user3"]
        for username in usernames:
            repo.create(username=username, email=f"{username}@example.com", hashed_password="hash", is_active=True)

        users = repo.get_in("username", usernames)

        assert len(users) == 3
        assert {u.username for u in users} == set(usernames)
