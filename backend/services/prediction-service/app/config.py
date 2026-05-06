"""
Prediction Service Configuration
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    SERVICE_NAME: str = "prediction-service"
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/prediction_db"

    # Redis
    REDIS_URL: str = "redis://:redis123@localhost:6379/2"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://rabbitmq:rabbitmq123@localhost:5672/"

    # Celery
    CELERY_BROKER_URL: str = "redis://:redis123@localhost:6379/3"
    CELERY_RESULT_BACKEND: str = "redis://:redis123@localhost:6379/3"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "skin-disease-images"
    MINIO_SECURE: bool = False

    # ML Model
    MODEL_PATH: str = "/app/models/final_model_CAS.pth"
    CLASS_MAPPING_PATH: str = "/app/models/class_mapping_ru.json"
    IMG_SIZE: int = 224

    # Disease malignancy mapping
    MALIGNANCY_MAP: dict = {
        "Меланома": True,
        "Базальноклеточная карцинома": True,
        "Плоскоклеточная карцинома": True,
        "Актинический кератоз": True,
        "Невус (родинка)": False,
        "Себорейный кератоз": False,
    }

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
