"""
API Gateway Configuration
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    SERVICE_NAME: str = "api-gateway"
    VERSION: str = "1.0.0"

    # Service URLs
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    PREDICTION_SERVICE_URL: str = "http://localhost:8002"
    ADMIN_SERVICE_URL: str = "http://localhost:8003"

    # Redis
    REDIS_URL: str = "redis://:redis123@localhost:6379/0"

    # JWT Configuration
    JWT_SECRET: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100  # requests per window
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # Timeouts
    REQUEST_TIMEOUT: int = 30  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
