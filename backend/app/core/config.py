from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    # 数据库 - 开发环境使用SQLite
    if os.getenv("USE_POSTGRES") == "true":
        DATABASE_URL: str = "postgresql://admin:admin123@localhost:5432/test_platform"
    else:
        DATABASE_URL: str = "sqlite:///./test_platform.db"

    # Redis
    REDIS_URL: str = "redis://:redis123@localhost:6379/0"

    # JWT
    JWT_SECRET: str = "secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 86400

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