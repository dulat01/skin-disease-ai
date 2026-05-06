"""
Dashboard Router
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.statistics import StatisticsService
from app.schemas.admin import DashboardResponse, DailyStatisticsResponse, NotificationResponse

router = APIRouter(prefix="/api/v1/admin", tags=["Dashboard"])


@router.get("/dashboard", response_model=dict)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """
    Get admin dashboard overview.

    Returns today's stats, overall totals, and recent activity.
    """
    stats_service = StatisticsService(db)
    dashboard_data = await stats_service.get_dashboard_data()

    return {
        "success": True,
        "message": "Dashboard data retrieved",
        "data": DashboardResponse(**dashboard_data)
    }


@router.get("/statistics/daily", response_model=dict)
async def get_daily_statistics(
    start_date: Optional[date] = Query(None, description="Start date (default: 30 days ago)"),
    end_date: Optional[date] = Query(None, description="End date (default: today)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get daily statistics for a date range.

    Defaults to last 30 days if no dates specified.
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    stats_service = StatisticsService(db)
    statistics = await stats_service.get_daily_statistics_range(start_date, end_date)

    return {
        "success": True,
        "message": "Daily statistics retrieved",
        "data": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "items": [
                DailyStatisticsResponse(
                    id=str(s.id),
                    date=s.date,
                    total_users=s.total_users,
                    new_users=s.new_users,
                    active_users=s.active_users,
                    total_predictions=s.total_predictions,
                    successful_predictions=s.successful_predictions,
                    failed_predictions=s.failed_predictions,
                    avg_processing_time_ms=s.avg_processing_time_ms,
                    disease_distribution=s.disease_distribution,
                    malignant_count=s.malignant_count,
                    benign_count=s.benign_count,
                    feedback_count=s.feedback_count,
                    positive_feedback=s.positive_feedback,
                    negative_feedback=s.negative_feedback,
                )
                for s in statistics
            ]
        }
    }


@router.get("/notifications", response_model=dict)
async def get_notifications(
    include_read: bool = Query(False, description="Include read notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum notifications to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get admin notifications.

    Returns unread notifications by default.
    """
    stats_service = StatisticsService(db)
    notifications = await stats_service.get_notifications(include_read, limit)

    return {
        "success": True,
        "message": "Notifications retrieved",
        "data": {
            "items": [
                NotificationResponse(
                    id=str(n.id),
                    type=n.type,
                    title=n.title,
                    message=n.message,
                    priority=n.priority,
                    is_read=n.is_read,
                    is_dismissed=n.is_dismissed,
                    extra_data=n.extra_data,
                    created_at=n.created_at,
                    read_at=n.read_at,
                )
                for n in notifications
            ],
            "total": len(notifications)
        }
    }


@router.post("/notifications/{notification_id}/read", response_model=dict)
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a notification as read.
    """
    stats_service = StatisticsService(db)
    success = await stats_service.mark_notification_read(notification_id)

    if success:
        return {
            "success": True,
            "message": "Notification marked as read"
        }
    else:
        return {
            "success": False,
            "message": "Notification not found"
        }
