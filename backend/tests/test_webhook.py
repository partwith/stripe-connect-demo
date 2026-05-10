import uuid
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.vendor import Vendor, OnboardingStatus

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
