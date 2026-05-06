"""
Models Router - Model metrics and management
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.statistics import StatisticsService
from app.schemas.admin import ModelMetricsResponse

router = APIRouter(prefix="/api/v1/admin", tags=["Model Management"])


@router.get("/model/metrics", response_model=dict)
async def get_model_metrics(
    model_version: str = Query("1.0.0", description="Model version"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get model performance metrics.

    Returns accuracy, confidence distribution, and class-wise performance.
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    stats_service = StatisticsService(db)
    metrics = await stats_service.get_model_metrics(model_version, start_date, end_date)

    # Aggregate metrics
    if metrics:
        total_predictions = sum(m.total_predictions for m in metrics)
        total_feedback = sum(m.feedback_count for m in metrics)
        total_correct = sum(m.correct_predictions for m in metrics)

        avg_confidence = None
        if total_predictions > 0:
            weighted_conf = sum((m.avg_confidence or 0) * m.total_predictions for m in metrics)
            avg_confidence = weighted_conf / total_predictions

        accuracy = None
        if total_feedback > 0:
            accuracy = total_correct / total_feedback

        aggregated = {
            "model_version": model_version,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_predictions": total_predictions,
            "avg_confidence": avg_confidence,
            "min_confidence": min((m.min_confidence for m in metrics if m.min_confidence), default=None),
            "max_confidence": max((m.max_confidence for m in metrics if m.max_confidence), default=None),
            "feedback_count": total_feedback,
            "correct_predictions": total_correct,
            "accuracy": accuracy,
            "daily_metrics": [
                {
                    "date": m.date.isoformat(),
                    "predictions": m.total_predictions,
                    "avg_confidence": m.avg_confidence,
                    "accuracy": m.accuracy
                }
                for m in metrics
            ]
        }
    else:
        aggregated = {
            "model_version": model_version,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_predictions": 0,
            "avg_confidence": None,
            "min_confidence": None,
            "max_confidence": None,
            "feedback_count": 0,
            "correct_predictions": 0,
            "accuracy": None,
            "daily_metrics": []
        }

    return {
        "success": True,
        "message": "Model metrics retrieved",
        "data": aggregated
    }


@router.get("/model/classes", response_model=dict)
async def get_class_distribution(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get prediction class distribution.

    Shows how many predictions each disease class received.
    """
    start_date = date.today() - timedelta(days=days)
    end_date = date.today()

    stats_service = StatisticsService(db)
    statistics = await stats_service.get_daily_statistics_range(start_date, end_date)

    # Aggregate class distribution
    distribution = {}
    total_malignant = 0
    total_benign = 0

    for stat in statistics:
        if stat.disease_distribution:
            for disease, count in stat.disease_distribution.items():
                distribution[disease] = distribution.get(disease, 0) + count
        total_malignant += stat.malignant_count
        total_benign += stat.benign_count

    total_predictions = sum(distribution.values())

    # Calculate percentages
    distribution_with_pct = {
        disease: {
            "count": count,
            "percentage": (count / total_predictions * 100) if total_predictions > 0 else 0
        }
        for disease, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True)
    }

    return {
        "success": True,
        "message": "Class distribution retrieved",
        "data": {
            "period_days": days,
            "total_predictions": total_predictions,
            "malignant_count": total_malignant,
            "benign_count": total_benign,
            "malignant_percentage": (total_malignant / total_predictions * 100) if total_predictions > 0 else 0,
            "distribution": distribution_with_pct
        }
    }
