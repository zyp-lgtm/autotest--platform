from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List
import os
import secrets
import logging

logger = logging.getLogger(__name__)


def get_default_jwt_secret() -> str:
    """
    获取安全的 JWT 密钥

    优先从环境变量读取，否则生成安全密钥
    生产环境必须设置 JWT_SECRET 环境变量
    """
    jwt_secret = os.getenv("JWT_SECRET")
    if jwt_secret:
        return jwt_secret

    # 开发环境使用生成的密钥
    logger.warning(
        "⚠️  警告: 使用自动生成的 JWT_SECRET。"
        "生产环境必须设置 JWT_SECRET 环境变量！"
    )
    return secrets.token_urlsafe(32)


class Settings(BaseSettings):
    # 数据库 - 开发环境使用SQLite
    if os.getenv("USE_POSTGRES") == "true":
        DATABASE_URL: str = "postgresql://admin:admin123@localhost:5432/test_platform"
    else:
        DATABASE_URL: str = "sqlite:///./test_platform.db"

    # Redis
    REDIS_URL: str = "redis://:redis123@localhost:6379/0"

    # JWT - 安全配置
    JWT_SECRET: str = get_default_jwt_secret()
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 86400  # 24 小时

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",  # Vite默认端口
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_ignore_empty=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()