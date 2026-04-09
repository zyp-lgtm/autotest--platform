"""
配置和 JWT 工具单元测试
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from app.core.config import Settings, get_settings


class TestSettings:
    """Settings 类测试"""

    def test_default_settings(self):
        """测试默认设置"""
        settings = Settings()

        assert settings.ENV == "development"
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'JWT_SECRET')
        assert hasattr(settings, 'BACKEND_CORS_ORIGINS')

    def test_jwt_secret_generation(self):
        """测试 JWT_SECRET 生成"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            # JWT_SECRET 应该被生成（长度至少 32）
            assert len(settings.JWT_SECRET) >= 32
            # 应该是 URL 安全的字符串
            assert settings.JWT_SECRET.isalnum() or '-' in settings.JWT_SECRET or '_' in settings.JWT_SECRET

    def test_jwt_secret_from_env(self):
        """测试从环境变量读取 JWT_SECRET"""
        test_secret = "my-test-secret-key-12345"

        with patch.dict(os.environ, {'JWT_SECRET': test_secret}):
            settings = Settings()
            assert settings.JWT_SECRET == test_secret

    def test_database_url_default(self):
        """测试默认数据库 URL"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            # 默认应该是 SQLite
            assert settings.DATABASE_URL.startswith("sqlite:///")

    def test_database_url_from_env(self):
        """测试从环境变量读取 DATABASE_URL"""
        test_url = "postgresql://user:pass@localhost/db"

        with patch.dict(os.environ, {'DATABASE_URL': test_url}):
            settings = Settings()
            assert settings.DATABASE_URL == test_url

    def test_cors_origins_default(self):
        """测试默认 CORS 来源"""
        settings = Settings()
        # 默认应该包含 localhost
        assert any("localhost" in origin for origin in settings.BACKEND_CORS_ORIGINS)

    def test_settings_singleton(self):
        """测试 Settings 单例"""
        settings1 = get_settings()
        settings2 = get_settings()

        # 应该返回同一个实例
        assert settings1 is settings2


class TestJWTConfig:
    """JWT 配置测试"""

    def test_jwt_algorithm(self):
        """测试 JWT 算法配置"""
        settings = Settings()
        assert settings.JWT_ALGORITHM in ["HS256", "HS384", "HS512"]

    def test_jwt_expiration(self):
        """测试 JWT 过期时间"""
        settings = Settings()
        # 默认应该有 ACCESS_TOKEN_EXPIRE_MINUTES
        assert hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES')
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0


@pytest.mark.integration
class TestConfigIntegration:
    """配置集成测试"""

    def test_env_file_loading(self):
        """测试 .env 文件加载"""
        # 检查是否存在 .env 文件
        import os
        env_path = os.path.join(os.path.dirname(__file__), '../../.env')

        if os.path.exists(env_path):
            settings = Settings()
            # 如果有 .env 文件，应该加载成功
            assert settings is not None

    def test_production_config(self):
        """测试生产环境配置"""
        with patch.dict(os.environ, {'ENV': 'production'}):
            settings = Settings()
            assert settings.ENV == "production"

    def test_development_config(self):
        """测试开发环境配置"""
        with patch.dict(os.environ, {'ENV': 'development'}):
            settings = Settings()
            assert settings.ENV == "development"
