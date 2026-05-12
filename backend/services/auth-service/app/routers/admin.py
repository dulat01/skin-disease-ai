"""
Admin Router - doctor and subscription management for admins
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Doctor, SubscriptionRequest, Subscription, SubscriptionPlan
from app.services.doctor import DoctorService, SubscriptionService

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/doctors", response_model=dict)
async def list_doctors(
    verified_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Admin: list all doctors or only verified doctors"""
    try:
        query = select(Doctor)
        if verified_only:
            query = query.where(Doctor.is_verified == True)

        result = await db.execute(query)
        doctors = result.scalars().all()

        return {
            "success": True,
            "message": "Doctors retrieved successfully",
            "data": [
                {
                    "id": str(doctor.id),
                    "email": doctor.email,
                    "full_name": doctor.full_name,
                    "license_number": doctor.license_number,
                    "specialization": doctor.specialization,
                    "is_verified": doctor.is_verified,
                    "created_at": doctor.created_at.isoformat() if doctor.created_at else None
                }
                for doctor in doctors
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/doctors/{doctor_id}/verify", response_model=dict)
async def verify_doctor(
    doctor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Admin: verify a doctor account"""
    try:
        doctor = await db.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found"
            )

        doctor.is_verified = True
        await db.commit()
        await db.refresh(doctor)

        return {
            "success": True,
            "message": "Doctor verified successfully",
            "data": {
                "id": str(doctor.id),
                "email": doctor.email,
                "full_name": doctor.full_name,
                "is_verified": doctor.is_verified
            }
        }
    except Exception as e:
        await db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/subscription-requests", response_model=dict)
async def list_subscription_requests(
    status_filter: str = "pending",
    db: AsyncSession = Depends(get_db)
):
    """Admin: list subscription requests"""
    try:
        query = select(SubscriptionRequest).where(
            SubscriptionRequest.status == status_filter
        )

        result = await db.execute(query)
        requests = result.scalars().all()

        return {
            "success": True,
            "message": "Subscription requests retrieved successfully",
            "data": [
                {
                    "id": str(req.id),
                    "user_id": str(req.user_id) if req.user_id else None,
                    "plan_id": str(req.plan_id),
                    "status": req.status,
                    "email": req.email,
                    "contact_phone": req.contact_phone,
                    "created_at": req.created_at.isoformat() if req.created_at else None
                }
                for req in requests
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/subscription-requests/{request_id}/approve", response_model=dict)
async def approve_subscription_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Admin: approve a subscription request"""
    try:
        req = await db.get(SubscriptionRequest, request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription request not found"
            )

        req.status = "approved"

        # Only create subscription if user_id exists (not anonymous request)
        if req.user_id:
            plan = await db.get(SubscriptionPlan, req.plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subscription plan not found"
                )

            subscription = Subscription(
                user_id=req.user_id,
                plan_id=req.plan_id,
                is_active=True
            )
            db.add(subscription)

        await db.commit()
        await db.refresh(req)

        return {
            "success": True,
            "message": "Subscription request approved successfully",
            "data": {
                "id": str(req.id),
                "status": req.status,
                "user_id": str(req.user_id) if req.user_id else None
            }
        }
    except Exception as e:
        await db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/subscription-requests/{request_id}/decline", response_model=dict)
async def decline_subscription_request(
    request_id: UUID,
    reason: str = "Request declined",
    db: AsyncSession = Depends(get_db)
):
    """Admin: decline a subscription request"""
    try:
        req = await db.get(SubscriptionRequest, request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription request not found"
            )

        req.status = "declined"
        await db.commit()
        await db.refresh(req)

        return {
            "success": True,
            "message": "Subscription request declined successfully",
            "data": {
                "id": str(req.id),
                "status": req.status,
                "reason": reason
            }
        }
    except Exception as e:
        await db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
