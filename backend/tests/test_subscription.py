# backend/tests/test_subscription.py
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.subscription import PLAN_CONFIG, Subscription, SubscriptionStatus, SubscriptionTier

TEST_DB_URL = "sqlite:///./test_subscription.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ADMIN_KEY = settings.admin_api_key


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _mock_stripe_customer(cus_id: str = "cus_test123") -> MagicMock:
    m = MagicMock()
    m.id = cus_id
    return m


def _mock_stripe_pi(pi_id: str = "pi_sub_test") -> MagicMock:
    m = MagicMock()
    m.id = pi_id
    return m


def test_create_subscription_basic(client):
    with (
        patch("app.routers.subscription.stripe_service.create_stripe_customer", return_value=_mock_stripe_customer()) as mock_cus,
        patch("app.routers.subscription.stripe_service.charge_subscription", return_value=_mock_stripe_pi()) as mock_pi,
    ):
        resp = client.post("/api/subscriptions/", json={"email": "user@example.com", "plan_tier": "basic"})

    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "user@example.com"
    assert data["plan_tier"] == "basic"
    assert data["plan_amount_cents"] == 1000
    assert data["ai_prompt_usage_limit"] == 100
    assert data["ai_prompt_usage_used"] == 0
    assert data["status"] == "active"
    assert data["stripe_customer_id"] == "cus_test123"
    assert data["stripe_payment_intent_id"] == "pi_sub_test"
    assert "idempotency_key" in data
    assert data["idempotency_key"] != ""
    mock_cus.assert_called_once_with(email="user@example.com")
    mock_pi.assert_called_once_with(
        stripe_customer_id="cus_test123",
        amount_cents=1000,
        idempotency_key=data["idempotency_key"],
    )


def test_create_subscription_standard(client):
    with (
        patch("app.routers.subscription.stripe_service.create_stripe_customer", return_value=_mock_stripe_customer("cus_std")),
        patch("app.routers.subscription.stripe_service.charge_subscription", return_value=_mock_stripe_pi("pi_std")),
    ):
        resp = client.post("/api/subscriptions/", json={"email": "std@example.com", "plan_tier": "standard"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["plan_amount_cents"] == 4000
    assert data["ai_prompt_usage_limit"] == 500


def test_create_subscription_premium(client):
    with (
        patch("app.routers.subscription.stripe_service.create_stripe_customer", return_value=_mock_stripe_customer("cus_prem")),
        patch("app.routers.subscription.stripe_service.charge_subscription", return_value=_mock_stripe_pi("pi_prem")),
    ):
        resp = client.post("/api/subscriptions/", json={"email": "prem@example.com", "plan_tier": "premium"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["plan_amount_cents"] == 10000
    assert data["ai_prompt_usage_limit"] == 2000


def test_subscription_billing_dates(client):
    with (
        patch("app.routers.subscription.stripe_service.create_stripe_customer", return_value=_mock_stripe_customer()),
        patch("app.routers.subscription.stripe_service.charge_subscription", return_value=_mock_stripe_pi()),
    ):
        resp = client.post("/api/subscriptions/", json={"email": "dates@example.com", "plan_tier": "basic"})
    assert resp.status_code == 201
    data = resp.json()

    starts_at = datetime.fromisoformat(data["starts_at"])
    expires_at = datetime.fromisoformat(data["expires_at"])
    next_charge_due_at = datetime.fromisoformat(data["next_charge_due_at"])

    assert (expires_at - starts_at).days == 365
    assert (expires_at - next_charge_due_at).days == 3


def test_create_subscription_invalid_tier(client):
    resp = client.post("/api/subscriptions/", json={"email": "bad@example.com", "plan_tier": "gold"})
    assert resp.status_code == 422


def test_create_subscription_stripe_failure_rolls_back(client):
    with (
        patch("app.routers.subscription.stripe_service.create_stripe_customer", return_value=_mock_stripe_customer()),
        patch("app.routers.subscription.stripe_service.charge_subscription", side_effect=Exception("card_declined")),
    ):
        resp = client.post("/api/subscriptions/", json={"email": "fail@example.com", "plan_tier": "basic"})
    assert resp.status_code == 400

    db = TestingSessionLocal()
    count = db.query(Subscription).count()
    db.close()
    assert count == 0


def test_create_subscription_idempotency_key_unique_per_call(client):
    keys = []
    for i in range(2):
        with (
            patch("app.routers.subscription.stripe_service.create_stripe_customer", return_value=_mock_stripe_customer(f"cus_{i}")),
            patch("app.routers.subscription.stripe_service.charge_subscription", return_value=_mock_stripe_pi(f"pi_{i}")),
        ):
            resp = client.post("/api/subscriptions/", json={"email": f"u{i}@example.com", "plan_tier": "basic"})
        assert resp.status_code == 201
        keys.append(resp.json()["idempotency_key"])
    assert keys[0] != keys[1]


def test_admin_list_subscriptions_requires_auth(client):
    resp = client.get("/api/admin/subscriptions")
    assert resp.status_code == 401


def test_admin_list_subscriptions(client):
    with (
        patch("app.routers.subscription.stripe_service.create_stripe_customer", return_value=_mock_stripe_customer("cus_adm")),
        patch("app.routers.subscription.stripe_service.charge_subscription", return_value=_mock_stripe_pi("pi_adm")),
    ):
        client.post("/api/subscriptions/", json={"email": "admin_test@example.com", "plan_tier": "premium"})

    resp = client.get("/api/admin/subscriptions", headers={"X-Admin-Key": ADMIN_KEY})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    sub = data["subscriptions"][0]
    assert sub["email"] == "admin_test@example.com"
    assert sub["plan_tier"] == "premium"
    assert sub["ai_prompt_usage_limit"] == 2000
    assert sub["status"] == "active"
    assert "expires_at" in sub
    assert "next_charge_due_at" in sub
