"""
Doctors Router - doctor registration and subscription management
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    DoctorRegister,
    DoctorLogin,
    SubscriptionRequestCreate,
    SubscriptionRequestResponse,
    SubscriptionResponse,
    SubscriptionPlanResponse
)
from app.services.doctor import DoctorService, SubscriptionService
from app.services.jwt import jwt_service

router = APIRouter(prefix="/api/v1/doctors", tags=["Doctors"])


@router.post("/register", response_model=dict)
async def register_doctor(
    doctor_data: DoctorRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new doctor account"""
    doctor_service = DoctorService(db)

    # Check if email already exists
    existing = await doctor_service.get_by_email(doctor_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    doctor = await doctor_service.create_doctor(doctor_data)

    return {
        "success": True,
        "message": "Doctor registration submitted. Awaiting admin verification.",
        "data": {
            "id": str(doctor.id),
            "email": doctor.email,
            "full_name": doctor.full_name,
            "license_number": doctor.license_number,
            "is_verified": doctor.is_verified,
        }
    }


@router.post("/login", response_model=dict)
async def login_doctor(
    credentials: DoctorLogin,
    db: AsyncSession = Depends(get_db)
):
    """Doctor login"""
    doctor_service = DoctorService(db)

    doctor = await doctor_service.get_by_email(credentials.email)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not jwt_service.verify_password(credentials.password, doctor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not doctor.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor account not verified by admin yet"
        )

    # Generate tokens
    tokens = jwt_service.create_tokens(
        user_id=str(doctor.id),
        email=doctor.email,
        is_admin=False
    )

    return {
        "success": True,
        "message": "Doctor logged in successfully",
        "data": {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
            "doctor": {
                "id": str(doctor.id),
                "email": doctor.email,
                "full_name": doctor.full_name,
                "specialization": doctor.specialization,
            }
        }
    }


@router.get("/plans", response_model=dict)
async def get_subscription_plans(db: AsyncSession = Depends(get_db)):
    """Get all available subscription plans"""
    subscription_service = SubscriptionService(db)
    await subscription_service.get_or_create_plans()

    plans = await subscription_service.get_plans()

    return {
        "success": True,
        "message": "Subscription plans retrieved",
        "data": [SubscriptionPlanResponse.model_validate(p.to_dict()) for p in plans]
    }


@router.post("/subscription/request", response_model=dict)
async def request_subscription(
    request_data: SubscriptionRequestCreate,
    user_id: UUID = Depends(lambda: None),  # Will be set by middleware
    db: AsyncSession = Depends(get_db)
):
    """User: request a subscription"""
    # Get user_id from request context (would be set by auth middleware in real app)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    subscription_service = SubscriptionService(db)
    req = await subscription_service.create_request(user_id, request_data)

    return {
        "success": True,
        "message": "Subscription request submitted. We will contact you soon.",
        "data": SubscriptionRequestResponse.model_validate(req.to_dict())
    }


@router.get("/subscription/status", response_model=dict)
async def get_subscription_status(
    user_id: UUID = Depends(lambda: None),
    db: AsyncSession = Depends(get_db)
):
    """User: check their subscription status"""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    subscription_service = SubscriptionService(db)
    sub = await subscription_service.get_user_subscription(user_id)

    if not sub:
        return {
            "success": True,
            "message": "No active subscription",
            "data": None
        }

    return {
        "success": True,
        "message": "Subscription status retrieved",
        "data": SubscriptionResponse.model_validate(sub.to_dict())
    }


@router.get("/dashboard/pending", response_model=dict)
async def get_pending_predictions(
    doctor_id: UUID = Depends(lambda: None),
    db: AsyncSession = Depends(get_db)
):
    """Doctor: get pending predictions for review"""
    if not doctor_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # This will be called by prediction service to get pending predictions
    # For now, return placeholder that prediction service will populate
    return {
        "success": True,
        "message": "Pending predictions retrieved",
        "data": []
    }


@router.post("/predictions/{prediction_id}/approve", response_model=dict)
async def approve_prediction(
    prediction_id: UUID,
    approval_data: dict,
    doctor_id: UUID = Depends(lambda: None),
    db: AsyncSession = Depends(get_db)
):
    """Doctor: approve a prediction with recommendations"""
    if not doctor_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # This endpoint will be implemented to call prediction service
    # and update the prediction with doctor approval
    return {
        "success": True,
        "message": "Prediction approved",
        "data": {
            "prediction_id": str(prediction_id),
            "doctor_id": str(doctor_id),
            "approved": True,
            "notes": approval_data.get("notes", "")
        }
    }
