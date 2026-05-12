"""
Public endpoints (no authentication required)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import SubscriptionPlanResponse, SubscriptionRequestCreate, SubscriptionRequestResponse
from app.services.doctor import SubscriptionService

router = APIRouter(prefix="/api/v1/public", tags=["Public"])


@router.get("/subscription/plans", response_model=dict)
async def get_subscription_plans(db: AsyncSession = Depends(get_db)):
    """Get all available subscription plans (public endpoint)"""
    subscription_service = SubscriptionService(db)
    await subscription_service.get_or_create_plans()

    plans = await subscription_service.get_plans()

    return {
        "success": True,
        "message": "Subscription plans retrieved",
        "data": [SubscriptionPlanResponse.model_validate(p.to_dict()) for p in plans]
    }


@router.post("/subscription/request", response_model=dict)
async def request_subscription_public(
    request_data: SubscriptionRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """Anonymous: request a subscription (no authentication required)"""
    subscription_service = SubscriptionService(db)
    req = await subscription_service.create_request(request_data, user_id=None)

    return {
        "success": True,
        "message": "Subscription request submitted. We will contact you soon.",
        "data": SubscriptionRequestResponse.model_validate(req.to_dict())
    }
