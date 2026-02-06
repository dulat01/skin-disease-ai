"""
Celery Application Configuration
"""
from celery import Celery

from app.config import settings

# Create Celery app
celery_app = Celery(
    "prediction_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.prediction_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_concurrency=2,
    result_expires=3600,  # 1 hour
)

# Task routes
celery_app.conf.task_routes = {
    "app.tasks.prediction_tasks.*": {"queue": "predictions"}
}
