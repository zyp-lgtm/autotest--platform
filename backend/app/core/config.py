from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "postgresql://admin:admin123@localhost:5432/test_platform"

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

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()