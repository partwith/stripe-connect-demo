import uuid
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.vendor import Vendor, OnboardingStatus
from app.models.order import Order, OrderStatus

TEST_DB_URL = "sqlite:///./test_webhook.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


@pytest.fixture
def vendor_in_db():
    db = TestingSessionLocal()
    vendor = Vendor(
        id=str(uuid.uuid4()),
        business_name="Webhook Vendor",
        email="webhook@example.com",
        stripe_account_id="acct_webhook123",
        onboarding_status=OnboardingStatus.IN_PROGRESS,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    db.close()
    return vendor


def make_mock_event(account_id: str, charges_enabled: bool, payouts_enabled: bool, details_submitted: bool = True):
    mock_event = MagicMock()
    mock_event.type = "account.updated"
    mock_event.data.object.id = account_id
    mock_event.data.object.charges_enabled = charges_enabled
    mock_event.data.object.payouts_enabled = payouts_enabled
    mock_event.data.object.details_submitted = details_submitted
    return mock_event


def test_webhook_account_updated_marks_complete(client, vendor_in_db):
    mock_event = make_mock_event("acct_webhook123", charges_enabled=True, payouts_enabled=True)
    with patch("app.routers.webhook.stripe_service.construct_webhook_event", return_value=mock_event):
        resp = client.post(
            "/api/webhooks/stripe",
            content=b'{"type":"account.updated"}',
            headers={"stripe-signature": "t=123,v1=abc"},
        )
    assert resp.status_code == 200
    assert resp.json() == {"received": True}

    db = TestingSessionLocal()
    updated = db.query(Vendor).filter_by(stripe_account_id="acct_webhook123").first()
    assert updated.onboarding_status == OnboardingStatus.COMPLETE
    assert updated.charges_enabled is True
    db.close()


def test_webhook_invalid_signature_returns_400(client):
    with patch(
        "app.routers.webhook.stripe_service.construct_webhook_event",
        side_effect=Exception("Invalid signature"),
    ):
        resp = client.post(
            "/api/webhooks/stripe",
            content=b'{}',
            headers={"stripe-signature": "invalid"},
        )
    assert resp.status_code == 400


def test_webhook_unknown_account_is_ignored(client):
    mock_event = make_mock_event("acct_unknown999", charges_enabled=True, payouts_enabled=True)
    with patch("app.routers.webhook.stripe_service.construct_webhook_event", return_value=mock_event):
        resp = client.post(
            "/api/webhooks/stripe",
            content=b'{"type":"account.updated"}',
            headers={"stripe-signature": "t=123,v1=abc"},
        )
    assert resp.status_code == 200
    assert resp.json() == {"received": True}


def test_webhook_unhandled_event_type_ignored(client):
    mock_event = MagicMock()
    mock_event.type = "payment_intent.created"
    with patch("app.routers.webhook.stripe_service.construct_webhook_event", return_value=mock_event):
        resp = client.post(
            "/api/webhooks/stripe",
            content=b'{"type":"payment_intent.created"}',
            headers={"stripe-signature": "t=123,v1=abc"},
        )
    assert resp.status_code == 200


@pytest.fixture
def order_in_db(vendor_in_db):
    db = TestingSessionLocal()
    order = Order(
        id=str(uuid.uuid4()),
        vendor_id=vendor_in_db.id,
        amount=10000,
        application_fee_amount=1000,
        idempotency_key=str(uuid.uuid4()),
        status=OrderStatus.PROCESSING,
        stripe_payment_intent_id="pi_webhook_test",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    order_id = order.id
    db.close()
    # Return a plain dict so the session is closed
    return {"id": order_id, "stripe_payment_intent_id": "pi_webhook_test"}


def make_pi_event(event_type: str, pi_id: str):
    mock_event = MagicMock()
    mock_event.type = event_type
    mock_event.data.object.id = pi_id
    return mock_event


def test_webhook_payment_intent_succeeded_marks_paid(client, order_in_db):
    mock_event = make_pi_event("payment_intent.succeeded", "pi_webhook_test")
    with patch("app.routers.webhook.stripe_service.construct_webhook_event", return_value=mock_event):
        resp = client.post(
            "/api/webhooks/stripe",
            content=b'{"type":"payment_intent.succeeded"}',
            headers={"stripe-signature": "t=123,v1=abc"},
        )
    assert resp.status_code == 200

    db = TestingSessionLocal()
    order = db.get(Order, order_in_db["id"])
    assert order.status == OrderStatus.PAID
    db.close()


def test_webhook_payment_intent_failed_marks_failed(client, order_in_db):
    mock_event = make_pi_event("payment_intent.payment_failed", "pi_webhook_test")
    with patch("app.routers.webhook.stripe_service.construct_webhook_event", return_value=mock_event):
        resp = client.post(
            "/api/webhooks/stripe",
            content=b'{"type":"payment_intent.payment_failed"}',
            headers={"stripe-signature": "t=123,v1=abc"},
        )
    assert resp.status_code == 200

    db = TestingSessionLocal()
    order = db.get(Order, order_in_db["id"])
    assert order.status == OrderStatus.FAILED
    db.close()


def test_webhook_payment_intent_succeeded_idempotent(client, order_in_db):
    """A second succeeded event on an already-paid order must not raise."""
    # First: mark as paid
    db = TestingSessionLocal()
    order = db.get(Order, order_in_db["id"])
    order.status = OrderStatus.PAID
    db.commit()
    db.close()

    mock_event = make_pi_event("payment_intent.succeeded", "pi_webhook_test")
    with patch("app.routers.webhook.stripe_service.construct_webhook_event", return_value=mock_event):
        resp = client.post(
            "/api/webhooks/stripe",
            content=b'{"type":"payment_intent.succeeded"}',
            headers={"stripe-signature": "t=123,v1=abc"},
        )
    assert resp.status_code == 200

    db = TestingSessionLocal()
    order = db.get(Order, order_in_db["id"])
    assert order.status == OrderStatus.PAID  # unchanged
    db.close()


def test_webhook_payment_failed_does_not_downgrade_paid(client, order_in_db):
    """A failed event must never overwrite a paid order."""
    db = TestingSessionLocal()
    order = db.get(Order, order_in_db["id"])
    order.status = OrderStatus.PAID
    db.commit()
    db.close()

    mock_event = make_pi_event("payment_intent.payment_failed", "pi_webhook_test")
    with patch("app.routers.webhook.stripe_service.construct_webhook_event", return_value=mock_event):
        resp = client.post(
            "/api/webhooks/stripe",
            content=b'{"type":"payment_intent.payment_failed"}',
            headers={"stripe-signature": "t=123,v1=abc"},
        )
    assert resp.status_code == 200

    db = TestingSessionLocal()
    order = db.get(Order, order_in_db["id"])
    assert order.status == OrderStatus.PAID  # must still be paid
    db.close()
