"""
认证 API 集成测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User


# 测试数据库
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """创建测试数据库引擎"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """创建测试数据库会话"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    # 创建表
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_client(test_db):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    from app.core.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aqxKGT5iqMWa",  # "password123"
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestAuthAPI:
    """认证 API 测试"""

    def test_register_new_user(self, test_client):
        """测试注册新用户"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_username(self, test_client, test_user):
        """测试注册重复用户名"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",  # 已存在
                "email": "different@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_missing_fields(self, test_client):
        """测试缺少必需字段"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser"
                # 缺少 email 和 password
            }
        )

        assert response.status_code == 422  # Validation error

    def test_login_valid_credentials(self, test_client, test_user):
        """测试使用有效凭证登录"""
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_username(self, test_client):
        """测试使用无效用户名登录"""
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent",
                "password": "password123"
            }
        )

        assert response.status_code == 401

    def test_login_invalid_password(self, test_client, test_user):
        """测试使用错误密码登录"""
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401

    def test_login_missing_fields(self, test_client):
        """测试缺少登录字段"""
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser"
                # 缺少 password
            }
        )

        assert response.status_code == 422

    def test_token_usage(self, test_client, test_user):
        """测试令牌使用"""
        # 首先登录获取令牌
        login_response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]

        # 使用令牌访问受保护的端点
        response = test_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_token_invalid(self, test_client):
        """测试使用无效令牌"""
        response = test_client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_token_missing(self, test_client):
        """测试缺少令牌"""
        response = test_client.get("/api/v1/users/me")

        assert response.status_code == 401


@pytest.mark.integration
class TestAuthAPIFlow:
    """认证流程集成测试"""

    def test_complete_auth_flow(self, test_client):
        """测试完整的认证流程"""
        # 1. 注册新用户
        register_response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "flowuser",
                "email": "flow@example.com",
                "password": "password123"
            }
        )
        assert register_response.status_code == 200
        token1 = register_response.json()["access_token"]

        # 2. 使用令牌访问受保护的资源
        me_response = test_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "flowuser"

        # 3. 登出并重新登录
        login_response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "flowuser",
                "password": "password123"
            }
        )
        assert login_response.status_code == 200
        token2 = login_response.json()["access_token"]

        # 4. 使用新令牌访问
        me_response2 = test_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert me_response2.status_code == 200
