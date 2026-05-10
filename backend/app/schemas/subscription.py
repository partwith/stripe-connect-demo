from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.subscription import SubscriptionStatus, SubscriptionTier


class SubscriptionCreate(BaseModel):
    email: EmailStr
    plan_tier: SubscriptionTier


class SubscriptionResponse(BaseModel):
    id: UUID
    email: str
    stripe_customer_id: str
    plan_tier: SubscriptionTier
    plan_amount_cents: int
    ai_prompt_usage_limit: int
    ai_prompt_usage_used: int
    status: SubscriptionStatus
    stripe_payment_intent_id: Optional[str]
    idempotency_key: str
    starts_at: datetime
    expires_at: datetime
    next_charge_due_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionListResponse(BaseModel):
    subscriptions: list[SubscriptionResponse]
    total: int
