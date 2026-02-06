"""
Auth Service Configuration
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    SERVICE_NAME: str = "auth-service"
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auth_db"

    # Redis
    REDIS_URL: str = "redis://:redis123@localhost:6379/1"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://rabbitmq:rabbitmq123@localhost:5672/"

    # JWT Configuration
    JWT_SECRET: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Password hashing
    BCRYPT_ROUNDS: int = 12

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
