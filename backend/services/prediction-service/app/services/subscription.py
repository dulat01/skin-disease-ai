"""
Subscription service - check user subscriptions and assign doctors
"""
import httpx
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.prediction import Prediction
import os

AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:8001')


class SubscriptionService:
    """Check subscriptions and manage doctor assignments"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_user_subscription(self, user_id: str) -> bool:
        """Check if user has active subscription via auth service"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{AUTH_SERVICE_URL}/api/v1/auth/subscription/status",
                    headers={"Authorization": f"Bearer {user_id}"}
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get('data') is not None
                return False
        except Exception as e:
            print(f"Error checking subscription: {e}")
            return False

    async def get_next_available_doctor(self) -> UUID:
        """Get next doctor using round-robin assignment"""
        try:
            from app.models import Doctor

            # Get all verified doctors
            stmt = select(Doctor).where(Doctor.is_verified == True)
            result = await self.db.execute(stmt)
            doctors = result.scalars().all()

            if not doctors:
                return None

            # If only one doctor, return it
            if len(doctors) == 1:
                return doctors[0].id

            # Round-robin: find doctor with least assigned predictions
            doctor_counts = {}
            for doctor in doctors:
                stmt = select(func.count(Prediction.id)).where(
                    Prediction.doctor_id == doctor.id,
                    Prediction.doctor_approved == None  # Not yet reviewed
                )
                result = await self.db.execute(stmt)
                count = result.scalar() or 0
                doctor_counts[doctor.id] = count

            # Return doctor with least pending predictions
            if doctor_counts:
                return min(doctor_counts, key=doctor_counts.get)

            return doctors[0].id if doctors else None

        except Exception as e:
            print(f"Error getting next doctor: {e}")
            return None
