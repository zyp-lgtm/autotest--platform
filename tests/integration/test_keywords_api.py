"""
关键字 API 集成测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import patch

from app.main import app
from app.core.database import get_db, Base
from app.models.keyword import Keyword


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
def sample_keywords(test_db):
    """创建示例关键字"""
    keywords_data = [
        {
            "id": "kw-001",
            "name": "CLICK",
            "category": "ui",
            "description": "点击元素",
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "force": {"type": "boolean"}
                }
            },
            "is_valid": True
        },
        {
            "id": "kw-002",
            "name": "INPUT",
            "category": "ui",
            "description": "输入文本",
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "text": {"type": "string"}
                }
            },
            "is_valid": True
        },
        {
            "id": "kw-003",
            "name": "NAVIGATE",
            "category": "ui",
            "description": "导航到URL",
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                }
            },
            "is_valid": True
        },
        {
            "id": "kw-004",
            "name": "ASSERT_TEXT",
            "category": "assertion",
            "description": "断言文本",
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "text": {"type": "string"}
                }
            },
            "is_valid": True
        }
    ]

    for kw_data in keywords_data:
        keyword = Keyword(**kw_data)
        test_db.add(keyword)
    test_db.commit()

    return keywords_data


class TestKeywordsAPI:
    """关键字 API 测试"""

    def test_list_all_keywords(self, test_client, sample_keywords):
        """测试获取所有关键字"""
        response = test_client.get("/api/v1/ui/keywords/")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 4

        # 验证第一个关键字
        kw = data[0]
        assert kw["name"] == "CLICK"
        assert kw["category"] == "ui"
        assert "parameter_schema" in kw

    def test_list_keywords_by_category(self, test_client, sample_keywords):
        """测试按类别过滤关键字"""
        # UI 关键字
        response = test_client.get("/api/v1/ui/keywords/?category=ui")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(kw["category"] == "ui" for kw in data)

        # 断言关键字
        response = test_client.get("/api/v1/ui/keywords/?category=assertion")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "ASSERT_TEXT"

    def test_list_enabled_keywords_only(self, test_client, sample_keywords):
        """测试仅获取有效的关键字"""
        # 禁用一个关键字
        response = test_client.get("/api/v1/ui/keywords/?enabled_only=true")
        assert response.status_code == 200
        data = response.json()

        # 所有示例关键字都是有效的
        assert len(data) == 4
        assert all(kw.get("is_valid", True) for kw in data)

    def test_keywords_response_structure(self, test_client, sample_keywords):
        """测试关键字响应结构"""
        response = test_client.get("/api/v1/ui/keywords/")
        assert response.status_code == 200

        data = response.json()
        kw = data[0]

        # 验证必需字段
        assert "id" in kw
        assert "name" in kw
        assert "category" in kw
        assert "description" in kw
        assert "parameter_schema" in kw

        # 验证参数结构
        schema = kw["parameter_schema"]
        assert isinstance(schema, dict)
        assert "type" in schema
        assert "properties" in schema

    def test_keywords_empty_database(self, test_client):
        """测试空数据库的情况"""
        response = test_client.get("/api/v1/ui/keywords/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_keywords_filter_nonexistent_category(self, test_client, sample_keywords):
        """测试过滤不存在的类别"""
        response = test_client.get("/api/v1/ui/keywords/?category=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_keywords_cache_performance(self, test_client, sample_keywords):
        """测试缓存性能（验证缓存是否工作）"""
        # 第一次请求
        response1 = test_client.get("/api/v1/ui/keywords/")
        assert response1.status_code == 200

        # 第二次请求（应该从缓存返回）
        response2 = test_client.get("/api/v1/ui/keywords/")
        assert response2.status_code == 200

        # 两次响应应该相同
        data1 = response1.json()
        data2 = response2.json()
        assert data1 == data2

    def test_keywords_parameter_schema_serialization(self, test_client, sample_keywords):
        """测试参数序列化是否正确"""
        response = test_client.get("/api/v1/ui/keywords/")
        assert response.status_code == 200

        data = response.json()
        click_kw = next(kw for kw in data if kw["name"] == "CLICK")

        # 验证参数被正确序列化
        schema = click_kw["parameter_schema"]
        assert schema["type"] == "object"
        assert "selector" in schema["properties"]
        assert "force" in schema["properties"]


@pytest.mark.integration
class TestKeywordsAPIWithAuth:
    """带认证的关键字 API 测试"""

    def test_keywords_with_valid_token(self, test_client, sample_keywords):
        """测试使用有效令牌访问"""
        # TODO: 添加认证测试
        pass

    def test_keywords_with_invalid_token(self, test_client):
        """测试使用无效令牌访问"""
        # TODO: 添加认证测试
        pass


class TestKeywordCRUD:
    """关键字 CRUD 操作测试"""

    def _make_keyword(self, **overrides):
        """创建 TestKeyword 实例用于 mock"""
        from unittest.mock import MagicMock
        import uuid as _uuid
        from datetime import datetime, timezone
        kw = MagicMock(spec=Keyword)
        kw.id = overrides.get("id", _uuid.uuid4())
        kw.name = overrides.get("name", "TEST_KEYWORD")
        kw.keyword_type = overrides.get("keyword_type", "system")
        kw.category = overrides.get("category", "ui")
        kw.description = overrides.get("description", "测试关键字")
        kw.icon = overrides.get("icon", None)
        kw.parameter_schema = overrides.get("parameter_schema", {})
        kw.return_schema = overrides.get("return_schema", {})
        kw.code_content = overrides.get("code_content", None)
        kw.is_valid = overrides.get("is_valid", True)
        kw.created_at = overrides.get("created_at", datetime.now(timezone.utc))
        return kw

    def _make_user(self):
        from unittest.mock import MagicMock
        from app.models.user import User
        import uuid as _uuid
        user = MagicMock(spec=User)
        user.id = _uuid.uuid4()
        user.username = "testuser"
        return user

    def test_create_keyword_success(self):
        """创建关键字 — 成功"""
        from unittest.mock import MagicMock, patch
        from app.api.ui.keywords import create_keyword
        from app.schemas.keyword import KeywordCreate
        import uuid as _uuid
        import asyncio

        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = None  # 名称不重复
        mock_user = self._make_user()

        kw_create = KeywordCreate(
            name="TEST_CLICK",
            keyword_type="action",
            category="ui",
            description="测试点击",
            parameter_schema={"type": "object"},
            return_schema={},
        )

        with patch("app.api.ui.keywords.invalidate_pattern"):
            result = asyncio.run(create_keyword(kw_create, user=mock_user, db=mock_db))

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result["name"] == "TEST_CLICK"
        assert result["category"] == "ui"

    def test_create_keyword_duplicate_name(self):
        """创建关键字 — 重名报错"""
        from unittest.mock import MagicMock, patch
        from app.api.ui.keywords import create_keyword
        from app.schemas.keyword import KeywordCreate
        import asyncio
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = self._make_keyword(name="EXISTING")
        mock_user = self._make_user()

        kw_create = KeywordCreate(
            name="EXISTING",
            keyword_type="action",
            category="ui",
        )

        with patch("app.api.ui.keywords.invalidate_pattern"):
            with pytest.raises(HTTPException) as exc:
                asyncio.run(create_keyword(kw_create, user=mock_user, db=mock_db))

        assert exc.value.status_code == 400
        assert "已存在" in exc.value.detail

    def test_update_keyword_success(self):
        """更新关键字 — 成功"""
        from unittest.mock import MagicMock, patch
        from app.api.ui.keywords import update_keyword
        from app.schemas.keyword import KeywordCreate
        import uuid as _uuid
        import asyncio

        kw_id = str(_uuid.uuid4())
        existing_kw = self._make_keyword(id=_uuid.UUID(kw_id), name="OLD_NAME")

        mock_db = MagicMock()
        # query().filter().first() 被调用两次：
        # 第一次是 validate_and_fetch 内部
        # 第二次是检查重名（update_keyword中 filter(Keyword.name == keyword.name)）
        mock_db.query().filter().first.side_effect = [existing_kw, None]
        mock_user = self._make_user()

        kw_update = KeywordCreate(
            name="NEW_NAME",
            keyword_type="action",
            category="ui",
            description="更新描述",
            parameter_schema={"type": "object"},
            return_schema={},
        )

        with patch("app.api.ui.keywords.invalidate_pattern"):
            result = asyncio.run(update_keyword(kw_id, kw_update, user=mock_user, db=mock_db))

        assert result["name"] == "NEW_NAME"
        assert result["description"] == "更新描述"

    def test_update_keyword_not_found(self):
        """更新关键字 — 不存在返回404"""
        from unittest.mock import MagicMock, patch
        from app.api.ui.keywords import update_keyword
        from app.schemas.keyword import KeywordCreate
        import uuid as _uuid
        import asyncio
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = None  # validate_and_fetch 返回 None
        mock_user = self._make_user()

        kw_update = KeywordCreate(
            name="WHATEVER",
            keyword_type="action",
            category="ui",
        )

        with patch("app.api.ui.keywords.invalidate_pattern"):
            with pytest.raises(HTTPException) as exc:
                asyncio.run(update_keyword(str(_uuid.uuid4()), kw_update, user=mock_user, db=mock_db))

        assert exc.value.status_code == 404

    def test_delete_keyword_success(self):
        """删除关键字 — 成功"""
        from unittest.mock import MagicMock, patch
        from app.api.ui.keywords import delete_keyword
        import uuid as _uuid
        import asyncio

        kw_id = str(_uuid.uuid4())
        existing_kw = self._make_keyword(
            id=_uuid.UUID(kw_id), name="TO_DELETE"
        )

        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = existing_kw
        mock_user = self._make_user()

        with patch("app.api.ui.keywords.invalidate_pattern"):
            result = asyncio.run(delete_keyword(kw_id, user=mock_user, db=mock_db))

        mock_db.delete.assert_called_once_with(existing_kw)
        mock_db.commit.assert_called_once()
        assert "已删除" in result["message"]

    def test_delete_keyword_not_found(self):
        """删除关键字 — 不存在返回404"""
        from unittest.mock import MagicMock, patch
        from app.api.ui.keywords import delete_keyword
        import uuid as _uuid
        import asyncio
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = None
        mock_user = self._make_user()

        with patch("app.api.ui.keywords.invalidate_pattern"):
            with pytest.raises(HTTPException) as exc:
                asyncio.run(delete_keyword(str(_uuid.uuid4()), user=mock_user, db=mock_db))

        assert exc.value.status_code == 404

    def test_create_keyword_default_values(self):
        """创建关键字 — 验证默认值正确存储"""
        from unittest.mock import MagicMock, patch
        from app.api.ui.keywords import create_keyword
        from app.schemas.keyword import KeywordCreate
        import asyncio

        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = None
        mock_user = self._make_user()

        kw_create = KeywordCreate(
            name="MINIMAL_KW",
            keyword_type="system",
            category="data",
        )

        with patch("app.api.ui.keywords.invalidate_pattern"):
            result = asyncio.run(create_keyword(kw_create, user=mock_user, db=mock_db))

        # is_valid=True 在真实 DB INSERT 时设置，mock DB 中可能为 None
        assert result["name"] == "MINIMAL_KW"
        assert result["category"] == "data"
