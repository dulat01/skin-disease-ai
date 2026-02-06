"""
Admin Service Configuration
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    SERVICE_NAME: str = "admin-service"
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/admin_db"

    # Redis
    REDIS_URL: str = "redis://:redis123@localhost:6379/4"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://rabbitmq:rabbitmq123@localhost:5672/"

    # Other services
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    PREDICTION_SERVICE_URL: str = "http://localhost:8002"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
