"""
Statistics Service
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.models.statistics import DailyStatistics, ModelMetrics, AdminNotification
from app.config import settings

logger = logging.getLogger(__name__)


class StatisticsService:
    """Service for managing statistics and dashboard data"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard overview data"""
        today = date.today()

        # Get today's statistics
        today_stats = await self.get_daily_statistics(today)

        # Get overall totals
        total_stats = await self._get_total_statistics()

        # Get recent model metrics
        model_metrics = await self.get_latest_model_metrics()

        # Get disease distribution (last 30 days)
        disease_dist = await self._get_disease_distribution(30)

        return {
            "today_predictions": today_stats.total_predictions if today_stats else 0,
            "today_users": today_stats.active_users if today_stats else 0,
            "today_feedback": today_stats.feedback_count if today_stats else 0,
            "total_users": total_stats.get("total_users", 0),
            "total_predictions": total_stats.get("total_predictions", 0),
            "total_feedback": total_stats.get("total_feedback", 0),
            "model_accuracy": model_metrics.accuracy if model_metrics else None,
            "avg_processing_time_ms": today_stats.avg_processing_time_ms if today_stats else None,
            "disease_distribution": disease_dist,
        }

    async def get_daily_statistics(self, target_date: date) -> Optional[DailyStatistics]:
        """Get statistics for a specific date"""
        result = await self.db.execute(
            select(DailyStatistics).where(DailyStatistics.date == target_date)
        )
        return result.scalar_one_or_none()

    async def get_daily_statistics_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[DailyStatistics]:
        """Get statistics for a date range"""
        result = await self.db.execute(
            select(DailyStatistics)
            .where(DailyStatistics.date >= start_date)
            .where(DailyStatistics.date <= end_date)
            .order_by(DailyStatistics.date.desc())
        )
        return list(result.scalars().all())

    async def get_or_create_daily_statistics(self, target_date: date) -> DailyStatistics:
        """Get or create statistics record for a date"""
        stats = await self.get_daily_statistics(target_date)
        if not stats:
            stats = DailyStatistics(date=target_date)
            self.db.add(stats)
            await self.db.flush()
            await self.db.refresh(stats)
        return stats

    async def update_daily_statistics(
        self,
        target_date: date,
        **kwargs
    ) -> DailyStatistics:
        """Update daily statistics"""
        stats = await self.get_or_create_daily_statistics(target_date)

        for key, value in kwargs.items():
            if hasattr(stats, key):
                setattr(stats, key, value)

        stats.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(stats)
        return stats

    async def increment_daily_stat(
        self,
        target_date: date,
        field: str,
        amount: int = 1
    ) -> None:
        """Increment a daily statistic field"""
        stats = await self.get_or_create_daily_statistics(target_date)
        current_value = getattr(stats, field, 0) or 0
        setattr(stats, field, current_value + amount)
        stats.updated_at = datetime.utcnow()
        await self.db.flush()

    async def get_latest_model_metrics(self) -> Optional[ModelMetrics]:
        """Get the latest model metrics"""
        result = await self.db.execute(
            select(ModelMetrics).order_by(ModelMetrics.date.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_model_metrics(
        self,
        model_version: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ModelMetrics]:
        """Get model metrics for a version"""
        query = select(ModelMetrics).where(ModelMetrics.model_version == model_version)

        if start_date:
            query = query.where(ModelMetrics.date >= start_date)
        if end_date:
            query = query.where(ModelMetrics.date <= end_date)

        query = query.order_by(ModelMetrics.date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_notifications(
        self,
        include_read: bool = False,
        limit: int = 50
    ) -> List[AdminNotification]:
        """Get admin notifications"""
        query = select(AdminNotification)

        if not include_read:
            query = query.where(AdminNotification.is_dismissed == False)

        query = query.order_by(AdminNotification.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_notification(
        self,
        type: str,
        title: str,
        message: str,
        priority: str = "normal",
        extra_data: Optional[Dict] = None
    ) -> AdminNotification:
        """Create a new notification"""
        notification = AdminNotification(
            type=type,
            title=title,
            message=message,
            priority=priority,
            extra_data=extra_data
        )
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        return notification

    async def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        from uuid import UUID
        result = await self.db.execute(
            select(AdminNotification).where(AdminNotification.id == UUID(notification_id))
        )
        notification = result.scalar_one_or_none()

        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await self.db.flush()
            return True
        return False

    async def _get_total_statistics(self) -> Dict[str, int]:
        """Get total aggregated statistics"""
        result = await self.db.execute(
            select(
                func.sum(DailyStatistics.total_users).label("total_users"),
                func.sum(DailyStatistics.total_predictions).label("total_predictions"),
                func.sum(DailyStatistics.feedback_count).label("total_feedback")
            )
        )
        row = result.one_or_none()

        if row:
            return {
                "total_users": row.total_users or 0,
                "total_predictions": row.total_predictions or 0,
                "total_feedback": row.total_feedback or 0
            }
        return {"total_users": 0, "total_predictions": 0, "total_feedback": 0}

    async def _get_disease_distribution(self, days: int = 30) -> Dict[str, int]:
        """Get disease distribution over recent days"""
        start_date = date.today() - timedelta(days=days)

        result = await self.db.execute(
            select(DailyStatistics.disease_distribution)
            .where(DailyStatistics.date >= start_date)
        )

        distribution = {}
        for row in result.scalars().all():
            if row:
                for disease, count in row.items():
                    distribution[disease] = distribution.get(disease, 0) + count

        return distribution

    async def fetch_users_from_auth_service(self) -> List[Dict]:
        """Fetch users from auth service"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.AUTH_SERVICE_URL}/api/v1/admin/users",
                    headers={"x-user-is-admin": "True"}
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {}).get("items", [])
        except Exception as e:
            logger.error(f"Failed to fetch users from auth service: {e}")
        return []
