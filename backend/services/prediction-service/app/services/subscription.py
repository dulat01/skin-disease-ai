"""
Doctor assignment service for predictions
"""
import httpx
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.prediction import Prediction
import os

AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:8001')


class SubscriptionService:
    """Manages doctor assignment for predictions"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_next_available_doctor(self) -> UUID:
        """Get next verified doctor from auth service using round-robin assignment"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{AUTH_SERVICE_URL}/api/v1/admin/doctors",
                    params={"verified_only": "true"}
                )
                if response.status_code != 200:
                    return None
                doctors = response.json().get("data", [])

            if not doctors:
                return None

            if len(doctors) == 1:
                return UUID(doctors[0]["id"])

            # Round-robin: pick doctor with fewest pending predictions
            doctor_counts = {}
            for doctor in doctors:
                doc_uuid = UUID(doctor["id"])
                stmt = select(func.count(Prediction.id)).where(
                    Prediction.doctor_id == doc_uuid,
                    Prediction.doctor_approved == None
                )
                result = await self.db.execute(stmt)
                doctor_counts[doc_uuid] = result.scalar() or 0

            return min(doctor_counts, key=doctor_counts.get)

        except Exception as e:
            print(f"Error getting next doctor: {e}")
            return None
