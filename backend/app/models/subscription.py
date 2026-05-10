import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Integer, String

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SubscriptionTier(str, enum.Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


PLAN_CONFIG = {
    SubscriptionTier.BASIC:    {"amount_cents": 1000,  "ai_prompt_usage_limit": 100},
    SubscriptionTier.STANDARD: {"amount_cents": 4000,  "ai_prompt_usage_limit": 500},
    SubscriptionTier.PREMIUM:  {"amount_cents": 10000, "ai_prompt_usage_limit": 2000},
}


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    plan_tier = Column(
        Enum(SubscriptionTier, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    plan_amount_cents = Column(Integer, nullable=False)
    ai_prompt_usage_limit = Column(Integer, nullable=False)
    ai_prompt_usage_used = Column(Integer, default=0, nullable=False)
    status = Column(
        Enum(SubscriptionStatus, values_callable=lambda x: [e.value for e in x]),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
    )
    stripe_payment_intent_id = Column(String(255), nullable=True, unique=True)
    idempotency_key = Column(String(255), nullable=False, unique=True)
    starts_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    next_charge_due_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
