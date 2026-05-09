"""
任务管理 API 自动化测试

测试任务 CRUD 操作：
- 创建任务
- 获取任务列表
- 获取单个任务
- 更新任务
- 删除任务
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """创建测试客户端"""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestTaskAPI:
    """任务 API 测试类"""

    def test_create_and_list_tasks(self, client):
        """测试创建任务和获取任务列表"""
        project_id = "test-project-123"

        # 创建任务1
        response = client.post(
            f"/v1/ui/tasks/?project_id={project_id}",
            json={
                "name": "测试任务1",
                "description": "这是第一个测试任务",
                "tags": ["测试", "自动化"]
            }
        )
        assert response.status_code == 200
        task1 = response.json()
        assert task1["name"] == "测试任务1"
        assert task1["tags"] == ["测试", "自动化"]
        task1_id = task1["id"]

        # 创建任务2
        response = client.post(
            f"/v1/ui/tasks/?project_id={project_id}",
            json={
                "name": "测试任务2",
                "description": "这是第二个测试任务",
                "tags": ["API测试"]
            }
        )
        assert response.status_code == 200
        task2 = response.json()
        task2_id = task2["id"]

        # 获取任务列表
        response = client.get(f"/v1/ui/tasks/?project_id={project_id}")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
        assert tasks[0]["name"] == "测试任务1"
        assert tasks[1]["name"] == "测试任务2"

    def test_get_task_by_id(self, client):
        """测试获取单个任务"""
        project_id = "test-project-456"

        # 创建任务
        response = client.post(
            f"/v1/ui/tasks/?project_id={project_id}",
            json={
                "name": "获取测试任务",
                "description": "用于测试获取单个任务"
            }
        )
        assert response.status_code == 200
        task = response.json()
        task_id = task["id"]

        # 获取任务
        response = client.get(f"/v1/ui/tasks/{task_id}")
        assert response.status_code == 200
        fetched_task = response.json()
        assert fetched_task["id"] == task_id
        assert fetched_task["name"] == "获取测试任务"

    def test_update_task(self, client):
        """测试更新任务"""
        project_id = "test-project-789"

        # 创建任务
        response = client.post(
            f"/v1/ui/tasks/?project_id={project_id}",
            json={
                "name": "原始任务名",
                "description": "原始描述",
                "tags": ["原始标签"]
            }
        )
        assert response.status_code == 200
        task = response.json()
        task_id = task["id"]

        # 更新任务
        response = client.put(
            f"/v1/ui/tasks/{task_id}",
            json={
                "name": "更新后的任务名",
                "description": "更新后的描述",
                "tags": ["更新后的标签"]
            }
        )
        assert response.status_code == 200
        updated_task = response.json()
        assert updated_task["name"] == "更新后的任务名"
        assert updated_task["description"] == "更新后的描述"
        assert updated_task["tags"] == ["更新后的标签"]

    def test_delete_task(self, client):
        """测试删除任务"""
        project_id = "test-project-delete"

        # 创建任务
        response = client.post(
            f"/v1/ui/tasks/?project_id={project_id}",
            json={
                "name": "待删除的任务",
                "description": "这个任务将被删除"
            }
        )
        assert response.status_code == 200
        task = response.json()
        task_id = task["id"]

        # 删除任务
        response = client.delete(f"/v1/ui/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "任务已删除"

        # 验证任务已删除
        response = client.get(f"/v1/ui/tasks/{task_id}")
        assert response.status_code == 404

    def test_get_nonexistent_task(self, client):
        """测试获取不存在的任务"""
        response = client.get("/v1/ui/tasks/nonexistent-id")
        assert response.status_code == 404

    def test_update_nonexistent_task(self, client):
        """测试更新不存在的任务"""
        response = client.put(
            "/v1/ui/tasks/nonexistent-id",
            json={"name": "新名字"}
        )
        assert response.status_code == 404

    def test_delete_nonexistent_task(self, client):
        """测试删除不存在的任务"""
        response = client.delete("/v1/ui/tasks/nonexistent-id")
        assert response.status_code == 404

    def test_task_validation(self, client):
        """测试任务验证"""
        project_id = "test-project-validation"

        # 测试空名称
        response = client.post(
            f"/v1/ui/tasks/?project_id={project_id}",
            json={
                "name": "",
                "description": "描述"
            }
        )
        # FastAPI 会自动验证，应该返回 422
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
