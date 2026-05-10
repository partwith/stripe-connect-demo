import uuid as _uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.subscription import PLAN_CONFIG, Subscription, SubscriptionStatus
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse
from app.services import stripe_service

router = APIRouter()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.post("/", response_model=SubscriptionResponse, status_code=201)
def create_subscription(body: SubscriptionCreate, db: Session = Depends(get_db)):
    tier = body.plan_tier
    config = PLAN_CONFIG[tier]
    idempotency_key = str(_uuid.uuid4())

    starts_at = _utcnow()
    expires_at = starts_at + timedelta(days=365)
    next_charge_due_at = expires_at - timedelta(days=3)

    customer = stripe_service.create_stripe_customer(email=body.email)

    sub = Subscription(
        email=body.email,
        stripe_customer_id=customer.id,
        plan_tier=tier,
        plan_amount_cents=config["amount_cents"],
        ai_prompt_usage_limit=config["ai_prompt_usage_limit"],
        ai_prompt_usage_used=0,
        status=SubscriptionStatus.ACTIVE,
        idempotency_key=idempotency_key,
        starts_at=starts_at,
        expires_at=expires_at,
        next_charge_due_at=next_charge_due_at,
    )
    db.add(sub)
    db.flush()

    try:
        pi = stripe_service.charge_subscription(
            stripe_customer_id=customer.id,
            amount_cents=config["amount_cents"],
            idempotency_key=idempotency_key,
        )
        sub.stripe_payment_intent_id = pi.id
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    db.commit()
    db.refresh(sub)
    return sub
