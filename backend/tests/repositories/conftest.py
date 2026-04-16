"""
Repository 层测试配置

提供测试 fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.user import User
from app.models.ui_task import UITask, UIScenario, UICase, UIStep
from app.models.keyword import Keyword
from app.models.execution import TestExecution, ScenarioExecution, CaseExecution, StepExecution
from app.repositories import (
    TaskRepository,
    ScenarioRepository,
    CaseRepository,
    StepRepository,
    ExecutionRepository,
    KeywordRepository,
    UserRepository
)


# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def engine():
    """创建测试数据库引擎"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def session(engine):
    """创建测试数据库会话"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def test_user(session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_keyword(session):
    """创建测试关键字"""
    keyword = Keyword(
        name="CLICK",
        category="interaction",
        description="Click on an element",
        parameter_schema={"selector": {"type": "string"}, "timeout": {"type": "integer"}},
        is_valid=True
    )
    session.add(keyword)
    session.commit()
    session.refresh(keyword)
    return keyword


@pytest.fixture(scope="function")
def test_task(session, test_user):
    """创建测试任务"""
    task = UITask(
        name="Test Task",
        description="A test task",
        task_type="ui",
        project_id=test_user.id,  # 使用 user.id 作为 project_id
        created_by=test_user.id
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture
def task_repository(session):
    """任务 Repository fixture"""
    return TaskRepository(session)


@pytest.fixture
def scenario_repository(session):
    """场景 Repository fixture"""
    return ScenarioRepository(session)


@pytest.fixture
def case_repository(session):
    """用例 Repository fixture"""
    return CaseRepository(session)


@pytest.fixture
def step_repository(session):
    """步骤 Repository fixture"""
    return StepRepository(session)


@pytest.fixture
def execution_repository(session):
    """执行 Repository fixture"""
    return ExecutionRepository(session)


@pytest.fixture
def keyword_repository(session):
    """关键字 Repository fixture"""
    return KeywordRepository(session)


@pytest.fixture
def user_repository(session):
    """用户 Repository fixture"""
    return UserRepository(session)
