"""
任务 API 集成测试
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User
from app.models.project import Project
from app.models.ui_task import UITask


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
def authenticated_user(test_db):
    """创建并认证用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aqxKGT5iqMWa",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_client, authenticated_user):
    """获取认证头"""
    response = test_client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_project(test_db, authenticated_user):
    """创建测试项目"""
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        description="Test project description",
        created_by=authenticated_user.id
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)
    return project


@pytest.fixture
def sample_task(test_db, test_project):
    """创建示例任务"""
    task = UITask(
        id=uuid.uuid4(),
        project_id=test_project.id,
        name="Sample Task",
        description="A sample test task",
        task_type="ui",
        scenario_ids=[],
        execution_config={},
        report_config={},
        tags=["test", "sample"],
        created_by=test_project.created_by
    )
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)
    return task


class TestTasksAPI:
    """任务 API 测试"""

    def test_list_tasks_requires_auth(self, test_client, test_project):
        """测试列出任务需要认证"""
        response = test_client.get(
            f"/api/v1/tasks?project_id={test_project.id}"
        )
        assert response.status_code == 401

    def test_list_tasks_empty(self, test_client, test_project, auth_headers):
        """测试列出空任务列表"""
        response = test_client.get(
            f"/api/v1/tasks?project_id={test_project.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_tasks_with_data(self, test_client, test_project, sample_task, auth_headers):
        """测试列出任务（有数据）"""
        response = test_client.get(
            f"/api/v1/tasks?project_id={test_project.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        task = data[0]
        assert task["name"] == "Sample Task"
        assert task["task_type"] == "ui"

    def test_create_task(self, test_client, test_project, auth_headers):
        """测试创建任务"""
        task_data = {
            "name": "New Task",
            "description": "New test task",
            "task_type": "ui",
            "tags": ["new"]
        }

        response = test_client.post(
            f"/api/v1/tasks?project_id={test_project.id}",
            json=task_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Task"
        assert data["task_type"] == "ui"
        assert "id" in data

    def test_create_task_missing_fields(self, test_client, test_project, auth_headers):
        """测试创建任务缺少必需字段"""
        task_data = {
            # 缺少 name
            "description": "Task without name"
        }

        response = test_client.post(
            f"/api/v1/tasks?project_id={test_project.id}",
            json=task_data,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_get_task(self, test_client, sample_task, auth_headers):
        """测试获取单个任务"""
        response = test_client.get(
            f"/api/v1/tasks/{sample_task.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_task.id)
        assert data["name"] == "Sample Task"

    def test_get_task_not_found(self, test_client, test_project, auth_headers):
        """测试获取不存在的任务"""
        fake_id = uuid.uuid4()
        response = test_client.get(
            f"/api/v1/tasks/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_task(self, test_client, sample_task, auth_headers):
        """测试更新任务"""
        update_data = {
            "name": "Updated Task Name",
            "description": "Updated description"
        }

        response = test_client.put(
            f"/api/v1/tasks/{sample_task.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Task Name"
        assert data["description"] == "Updated description"

    def test_delete_task(self, test_client, sample_task, auth_headers):
        """测试删除任务"""
        response = test_client.delete(
            f"/api/v1/tasks/{sample_task.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["detail"].lower()

        # 验证任务已删除
        get_response = test_client.get(
            f"/api/v1/tasks/{sample_task.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_unauthorized_task_access(self, test_client, sample_task):
        """测试未授权访问任务"""
        response = test_client.get(f"/api/v1/tasks/{sample_task.id}")
        assert response.status_code == 401

    def test_invalid_project_id(self, test_client, auth_headers):
        """测试无效的项目 ID"""
        response = test_client.get(
            "/api/v1/tasks?project_id=invalid-uuid",
            headers=auth_headers
        )
        assert response.status_code == 400


@pytest.mark.integration
class TestTasksAPIWithScenarios:
    """任务 API 场景集成测试"""

    def test_task_with_scenarios(self, test_client, test_project, auth_headers):
        """测试带场景的任务"""
        # 创建任务
        task_response = test_client.post(
            f"/api/v1/tasks?project_id={test_project.id}",
            json={
                "name": "Task with Scenarios",
                "task_type": "ui"
            },
            headers=auth_headers
        )
        task_id = task_response.json()["id"]

        # 创建场景
        scenario_response = test_client.post(
            f"/api/v1/ui/scenarios?task_id={task_id}",
            json={
                "name": "Test Scenario",
                "description": "A test scenario"
            },
            headers=auth_headers
        )

        assert scenario_response.status_code == 200
        scenario = scenario_response.json()
        assert scenario["name"] == "Test Scenario"

    def test_task_execution_flow(self, test_client, test_project, auth_headers):
        """测试任务执行流程"""
        # 创建任务
        task_response = test_client.post(
            f"/api/v1/tasks?project_id={test_project.id}",
            json={
                "name": "Executable Task",
                "task_type": "ui"
            },
            headers=auth_headers
        )
        task_id = task_response.json()["id"]

        # 执行任务
        execute_response = test_client.post(
            f"/api/v1/tasks/{task_id}/execute",
            headers=auth_headers
        )

        # 可能返回 202（已接受）或 200（成功），取决于实现
        assert execute_response.status_code in [200, 202]
