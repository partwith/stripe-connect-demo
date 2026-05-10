import uuid
from datetime import datetime, timedelta, timezone

from celery_worker import celery_app
from app.database import SessionLocal
from app.models.subscription import Subscription, SubscriptionStatus
from app.services import stripe_service


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@celery_app.task(name="app.tasks.subscription_tasks.renew_due_subscriptions")
def renew_due_subscriptions():
    db = SessionLocal()
    try:
        now = _utcnow()
        subs = (
            db.query(Subscription)
            .filter(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.next_charge_due_at <= now,
            )
            .all()
        )
        for sub in subs:
            new_key = str(uuid.uuid4())
            try:
                pi = stripe_service.charge_subscription(
                    stripe_customer_id=sub.stripe_customer_id,
                    amount_cents=sub.plan_amount_cents,
                    idempotency_key=new_key,
                )
                starts_at = _utcnow()
                expires_at = starts_at + timedelta(days=365)
                sub.starts_at = starts_at
                sub.expires_at = expires_at
                sub.next_charge_due_at = expires_at - timedelta(days=3)
                sub.ai_prompt_usage_used = 0
                sub.idempotency_key = new_key
                sub.stripe_payment_intent_id = pi.id
            except Exception:
                sub.status = SubscriptionStatus.EXPIRED
            db.commit()
    finally:
        db.close()
