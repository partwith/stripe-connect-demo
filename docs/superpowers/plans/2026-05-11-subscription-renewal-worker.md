# Subscription Renewal Worker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Celery Beat daily task that finds active subscriptions due for renewal, charges them via Stripe, resets their billing period, and marks failures as expired.

**Architecture:** New `subscription_tasks.py` follows the existing `vendor_tasks.py` pattern — `SessionLocal()` directly, try/finally close, per-row commit so one failure doesn't affect others. Stripe charge is reused from `stripe_service.charge_subscription()`. Celery Beat fires daily at UTC 00:00.

**Tech Stack:** Python 3.12, Celery 5, SQLAlchemy 2, Stripe SDK, pytest, unittest.mock

---

## File Map

| Action | Path |
|--------|------|
| Create | `backend/app/tasks/subscription_tasks.py` |
| Modify | `backend/celery_worker.py` |
| Modify | `backend/tests/test_subscription.py` |

---

### Task 1: Implement `renew_due_subscriptions` with tests

**Files:**
- Create: `backend/app/tasks/subscription_tasks.py`
- Modify: `backend/tests/test_subscription.py`

- [x] **Step 1: Add the renewal task tests to `test_subscription.py`**

Append these imports at the top of `backend/tests/test_subscription.py` (after existing imports):

```python
from app.tasks.subscription_tasks import renew_due_subscriptions
```

Then append the following helpers and test functions at the bottom of the file:

```python
# ── Renewal task helpers ──────────────────────────────────────────────────────

def _make_sub(db, *, next_charge_due_at, status=SubscriptionStatus.ACTIVE,
              email="r@example.com", used=50):
    sub = Subscription(
        id=str(uuid.uuid4()),
        email=email,
        stripe_customer_id="cus_renew",
        plan_tier=SubscriptionTier.BASIC,
        plan_amount_cents=1000,
        ai_prompt_usage_limit=100,
        ai_prompt_usage_used=used,
        status=status,
        idempotency_key=str(uuid.uuid4()),
        starts_at=datetime.utcnow() - timedelta(days=365),
        expires_at=datetime.utcnow() - timedelta(days=3),
        next_charge_due_at=next_charge_due_at,
        stripe_payment_intent_id="pi_old",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def _pi(pi_id="pi_renewed"):
    m = MagicMock()
    m.id = pi_id
    return m


# ── Renewal task tests ────────────────────────────────────────────────────────

def test_renewal_resets_billing_and_usage():
    db = TestingSessionLocal()
    sub = _make_sub(db, next_charge_due_at=datetime.utcnow() - timedelta(days=1))
    sub_id = sub.id
    db.close()

    with (
        patch("app.tasks.subscription_tasks.SessionLocal", TestingSessionLocal),
        patch("app.tasks.subscription_tasks.stripe_service.charge_subscription", return_value=_pi("pi_renewed")),
    ):
        renew_due_subscriptions()

    db = TestingSessionLocal()
    updated = db.query(Subscription).filter(Subscription.id == sub_id).first()
    db.close()

    assert updated.status == SubscriptionStatus.ACTIVE
    assert updated.ai_prompt_usage_used == 0
    assert updated.stripe_payment_intent_id == "pi_renewed"
    assert updated.expires_at > datetime.utcnow()
    assert (updated.expires_at - updated.starts_at).days == 365
    assert (updated.expires_at - updated.next_charge_due_at).days == 3


def test_renewal_stripe_failure_marks_expired():
    db = TestingSessionLocal()
    sub = _make_sub(db, next_charge_due_at=datetime.utcnow() - timedelta(days=1))
    sub_id = sub.id
    db.close()

    with (
        patch("app.tasks.subscription_tasks.SessionLocal", TestingSessionLocal),
        patch("app.tasks.subscription_tasks.stripe_service.charge_subscription",
              side_effect=Exception("card_declined")),
    ):
        renew_due_subscriptions()

    db = TestingSessionLocal()
    updated = db.query(Subscription).filter(Subscription.id == sub_id).first()
    db.close()

    assert updated.status == SubscriptionStatus.EXPIRED


def test_renewal_skips_not_yet_due():
    db = TestingSessionLocal()
    sub = _make_sub(db, next_charge_due_at=datetime.utcnow() + timedelta(days=10))
    sub_id = sub.id
    db.close()

    with (
        patch("app.tasks.subscription_tasks.SessionLocal", TestingSessionLocal),
        patch("app.tasks.subscription_tasks.stripe_service.charge_subscription", return_value=_pi()) as mock_charge,
    ):
        renew_due_subscriptions()

    mock_charge.assert_not_called()

    db = TestingSessionLocal()
    updated = db.query(Subscription).filter(Subscription.id == sub_id).first()
    db.close()
    assert updated.status == SubscriptionStatus.ACTIVE
    assert updated.ai_prompt_usage_used == 50


def test_renewal_skips_already_expired():
    db = TestingSessionLocal()
    sub = _make_sub(
        db,
        next_charge_due_at=datetime.utcnow() - timedelta(days=1),
        status=SubscriptionStatus.EXPIRED,
    )
    sub_id = sub.id
    db.close()

    with (
        patch("app.tasks.subscription_tasks.SessionLocal", TestingSessionLocal),
        patch("app.tasks.subscription_tasks.stripe_service.charge_subscription", return_value=_pi()) as mock_charge,
    ):
        renew_due_subscriptions()

    mock_charge.assert_not_called()


def test_renewal_one_failure_does_not_block_others():
    db = TestingSessionLocal()
    sub_fail = _make_sub(db, next_charge_due_at=datetime.utcnow() - timedelta(days=1),
                         email="fail@example.com")
    sub_ok = _make_sub(db, next_charge_due_at=datetime.utcnow() - timedelta(days=1),
                       email="ok@example.com")
    fail_id, ok_id = sub_fail.id, sub_ok.id
    db.close()

    call_count = 0
    def _side_effect(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("card_declined")
        return _pi(f"pi_{call_count}")

    with (
        patch("app.tasks.subscription_tasks.SessionLocal", TestingSessionLocal),
        patch("app.tasks.subscription_tasks.stripe_service.charge_subscription",
              side_effect=_side_effect),
    ):
        renew_due_subscriptions()

    db = TestingSessionLocal()
    failed = db.query(Subscription).filter(Subscription.id == fail_id).first()
    ok = db.query(Subscription).filter(Subscription.id == ok_id).first()
    db.close()

    assert failed.status == SubscriptionStatus.EXPIRED
    assert ok.status == SubscriptionStatus.ACTIVE
    assert ok.ai_prompt_usage_used == 0
```

- [x] **Step 2: Run the tests — confirm they all fail with ImportError**

Not applicable (tests were already added after the implementation was created in a prior session). Proceeded to Step 3.

- [x] **Step 3: Create `backend/app/tasks/subscription_tasks.py`**

File already existed with correct implementation from prior session.

- [x] **Step 4: Run all five renewal tests — confirm they pass**

```
test_renewal_resets_billing_and_usage PASSED
test_renewal_stripe_failure_marks_expired PASSED
test_renewal_skips_not_yet_due PASSED
test_renewal_skips_already_expired PASSED
test_renewal_one_failure_does_not_block_others PASSED
```

- [x] **Step 5: Run the full test suite — confirm nothing regressed**

`pytest tests/ -v` → 46 passed.

- [x] **Step 6: Commit**

```
git commit 4c8f837: feat: add subscription renewal Celery task with tests
```

---

### Task 2: Wire renewal task into Celery Beat

**Files:**
- Modify: `backend/celery_worker.py`

- [x] **Step 1: Update `celery_worker.py`**

Replaced entire file with `include=["app.tasks.vendor_tasks", "app.tasks.subscription_tasks"]` and added `renew-subscriptions-daily` beat schedule with `crontab(hour=0, minute=0)`.

- [x] **Step 2: Verify the worker can import the new task without errors**

```
from celery_worker import celery_app
import app.tasks.subscription_tasks
→ app.tasks.subscription_tasks.renew_due_subscriptions registered ✓
beat_schedule confirms: renew-subscriptions-daily at <crontab: 0 0 * * *>
```

- [x] **Step 3: Commit**

```
git commit: feat: wire subscription renewal task into Celery Beat (daily UTC 00:00)
```

---

✅ All steps complete.


