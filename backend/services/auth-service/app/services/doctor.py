"""
Doctor and subscription service
"""
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Doctor, Subscription, SubscriptionPlan, SubscriptionRequest
from app.schemas import DoctorRegister, SubscriptionRequestCreate
from app.services.jwt import jwt_service


class DoctorService:
    """Service for doctor-related operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_doctor(self, doctor_data: DoctorRegister) -> Doctor:
        """Register a new doctor"""
        hashed_password = jwt_service.hash_password(doctor_data.password)

        doctor = Doctor(
            email=doctor_data.email,
            hashed_password=hashed_password,
            full_name=doctor_data.full_name,
            license_number=doctor_data.license_number,
            specialization=doctor_data.specialization,
            phone=doctor_data.phone,
        )
        self.db.add(doctor)
        await self.db.commit()
        await self.db.refresh(doctor)
        return doctor

    async def get_by_email(self, email: str) -> Doctor:
        """Get doctor by email"""
        stmt = select(Doctor).where(Doctor.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def verify_doctor(self, doctor_id: UUID) -> bool:
        """Admin: verify a doctor account"""
        stmt = select(Doctor).where(Doctor.id == doctor_id)
        result = await self.db.execute(stmt)
        doctor = result.scalar_one_or_none()

        if not doctor:
            return False

        doctor.is_verified = True
        doctor.verified_at = datetime.utcnow()
        await self.db.commit()
        return True


class SubscriptionService:
    """Service for subscription management"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_plans(self) -> list[SubscriptionPlan]:
        """Get all subscription plans"""
        stmt = select(SubscriptionPlan)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_or_create_plans(self):
        """Ensure default plans exist"""
        plans = await self.get_plans()
        if len(plans) == 0:
            plans_data = [
                {"name": "1-month", "duration_days": "30", "description": "1 month subscription"},
                {"name": "3-month", "duration_days": "90", "description": "3 months subscription"},
                {"name": "6-month", "duration_days": "180", "description": "6 months subscription"},
            ]
            for plan_data in plans_data:
                plan = SubscriptionPlan(**plan_data)
                self.db.add(plan)
            await self.db.commit()

    async def create_request(self, request_data: SubscriptionRequestCreate, user_id: UUID = None) -> SubscriptionRequest:
        """Create a subscription purchase request (with optional user_id for anonymous requests)"""
        req = SubscriptionRequest(
            user_id=user_id,
            plan_id=UUID(request_data.plan_id),
            contact_info=request_data.contact_info,
            notes=request_data.notes,
            status="pending"
        )
        self.db.add(req)
        await self.db.commit()
        await self.db.refresh(req)
        return req

    async def get_user_subscription(self, user_id: UUID) -> Subscription:
        """Get active subscription for user"""
        stmt = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_active == True
        )
        result = await self.db.execute(stmt)
        sub = result.scalar_one_or_none()

        # Check if expired
        if sub and sub.end_date < datetime.utcnow():
            sub.is_active = False
            await self.db.commit()
            return None

        return sub

    async def activate_subscription(self, user_id: UUID, plan_id: UUID) -> Subscription:
        """Activate subscription for user (admin action)"""
        # Get plan
        stmt = select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        result = await self.db.execute(stmt)
        plan = result.scalar_one_or_none()

        if not plan:
            return None

        # Deactivate any existing subscription
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.is_active = False

        # Create new subscription
        duration = int(plan.duration_days)
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=duration)

        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def approve_subscription_request(self, request_id: UUID) -> SubscriptionRequest:
        """Admin: approve a subscription request and activate it"""
        stmt = select(SubscriptionRequest).where(SubscriptionRequest.id == request_id)
        result = await self.db.execute(stmt)
        req = result.scalar_one_or_none()

        if not req:
            return None

        req.status = "approved"
        req.processed_at = datetime.utcnow()

        # Activate subscription only if user_id exists
        if req.user_id:
            await self.activate_subscription(req.user_id, req.plan_id)
        await self.db.commit()
        await self.db.refresh(req)
        return req
