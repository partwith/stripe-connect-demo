# Subscription Renewal Worker — Design Spec

**Date:** 2026-05-11  
**Status:** Approved

## Problem

The subscription model stores `next_charge_due_at` (expires_at − 3 days) but no worker reads it. Renewals never fire — subscriptions expire silently.

## Scope

Add a Celery Beat periodic task that runs daily, finds subscriptions due for renewal, charges them off-session via Stripe, and resets their billing period. On charge failure, mark the subscription expired.

## Architecture

### New file: `backend/app/tasks/subscription_tasks.py`

One task: `renew_due_subscriptions`

**Query:** `status == active AND next_charge_due_at <= utcnow()`

**Per subscription:**
1. Generate a new `idempotency_key` (UUID4)
2. Call `stripe_service.charge_subscription(stripe_customer_id, plan_amount_cents, idempotency_key)`
3. **Success path:**
   - `starts_at = utcnow()`
   - `expires_at = starts_at + 365 days`
   - `next_charge_due_at = expires_at − 3 days`
   - `ai_prompt_usage_used = 0`
   - `stripe_payment_intent_id = pi.id`
   - `db.commit()`
4. **Failure path (any exception):**
   - `status = SubscriptionStatus.EXPIRED`
   - `db.commit()`
   - Continue to next subscription (do not raise)

Each subscription is committed independently — one failure does not roll back others.

### Updated: `backend/celery_worker.py`

- Add `app.tasks.subscription_tasks` to `include`
- Add beat schedule entry: daily at UTC 00:00

```python
"renew-subscriptions-daily": {
    "task": "app.tasks.subscription_tasks.renew_due_subscriptions",
    "schedule": crontab(hour=0, minute=0),
}
```

### No changes to `stripe_service.py`

`charge_subscription()` already works for this case — uses `pm_card_visa` (test) and `setup_future_usage="off_session"`.

## Data Flow

```
Celery Beat (daily 00:00 UTC)
  → renew_due_subscriptions()
      → DB query: active subs where next_charge_due_at <= now
      → for each sub:
          → stripe_service.charge_subscription()
          → success: reset billing window + usage
          → failure: mark expired
```

## Error Handling

- Stripe exceptions: caught per-subscription, mark expired, continue
- DB errors: not explicitly caught — will surface as task failure in Celery logs; Beat will retry on next schedule
- No retry logic for failed renewals (out of scope for demo)

## Testing

Add to existing `test_subscription.py`:
- Happy path: sub with `next_charge_due_at` in the past → after task runs, dates reset and usage cleared
- Failure path: Stripe raises → sub marked expired
- Not-yet-due: sub with `next_charge_due_at` in the future → untouched
- Already expired: skipped by query filter

## Out of Scope

- Email notifications on renewal or failure
- `past_due` status / retry logic
- Admin UI changes
