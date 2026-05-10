import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.vendor import Vendor, OnboardingStatus
from app.services.stripe_service import (
    create_express_account,
    create_account_link,
    get_account,
    construct_webhook_event,
)

# ── Model tests ──────────────────────────────────────────────────────────────

def test_vendor_model_fields():
    v = Vendor()
    for field in ["id", "business_name", "email", "stripe_account_id",
                  "onboarding_status", "charges_enabled", "payouts_enabled",
                  "details_submitted", "created_at", "updated_at"]:
        assert hasattr(v, field)


def test_onboarding_status_values():
    assert OnboardingStatus.PENDING == "pending"
    assert OnboardingStatus.IN_PROGRESS == "in_progress"
    assert OnboardingStatus.COMPLETE == "complete"
    assert OnboardingStatus.RESTRICTED == "restricted"


# ── Stripe service tests ──────────────────────────────────────────────────────

def test_create_express_account():
    mock_account = MagicMock()
    mock_account.id = "acct_test123"
    with patch("app.services.stripe_service.stripe.Account.create", return_value=mock_account) as mock_create:
        result = create_express_account(email="vendor@example.com", business_name="Test Corp")
        mock_create.assert_called_once_with(
            type="express",
            email="vendor@example.com",
            business_profile={"name": "Test Corp"},
            capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}},
        )
        assert result.id == "acct_test123"


def test_create_account_link():
    mock_link = MagicMock()
    mock_link.url = "https://connect.stripe.com/setup/e/abc123"
    with patch("app.services.stripe_service.stripe.AccountLink.create", return_value=mock_link):
        url = create_account_link(
            account_id="acct_test123",
            return_url="http://localhost:3000/return",
            refresh_url="http://localhost:8000/api/vendors/1/onboard",
        )
        assert url == "https://connect.stripe.com/setup/e/abc123"


def test_get_account():
    mock_account = MagicMock()
    mock_account.charges_enabled = True
    mock_account.payouts_enabled = False
    mock_account.details_submitted = True
    with patch("app.services.stripe_service.stripe.Account.retrieve", return_value=mock_account):
        account = get_account("acct_test123")
        assert account.charges_enabled is True


def test_construct_webhook_event_invalid_raises():
    with patch("app.services.stripe_service.stripe.Webhook.construct_event", side_effect=Exception("Invalid signature")):
        try:
            construct_webhook_event(b"{}", "bad_sig")
            assert False, "Should have raised"
        except Exception as e:
            assert "Invalid signature" in str(e)


# ── Vendor Router tests (SQLite in-memory) ───────────────────────────────────

from app.main import app
from app.database import Base, get_db

TEST_DB_URL = "sqlite:///./test_vendor.db"
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


def test_register_vendor_creates_stripe_account(client):
    mock_account = MagicMock()
    mock_account.id = "acct_test_abc"
    with patch("app.routers.vendor.stripe_service.create_express_account", return_value=mock_account):
        resp = client.post("/api/vendors/", json={"business_name": "Acme Corp", "email": "acme@example.com"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "acme@example.com"
    assert data["stripe_account_id"] == "acct_test_abc"
    assert data["onboarding_status"] == "pending"


def test_register_vendor_duplicate_email_returns_409(client):
    mock_account = MagicMock()
    mock_account.id = "acct_test_abc"
    with patch("app.routers.vendor.stripe_service.create_express_account", return_value=mock_account):
        client.post("/api/vendors/", json={"business_name": "Acme", "email": "dupe@example.com"})
    mock_account2 = MagicMock()
    mock_account2.id = "acct_test_xyz"
    with patch("app.routers.vendor.stripe_service.create_express_account", return_value=mock_account2):
        resp = client.post("/api/vendors/", json={"business_name": "Acme2", "email": "dupe@example.com"})
    assert resp.status_code == 409


def test_create_onboard_link(client):
    mock_account = MagicMock()
    mock_account.id = "acct_onboard"
    with patch("app.routers.vendor.stripe_service.create_express_account", return_value=mock_account):
        create_resp = client.post("/api/vendors/", json={"business_name": "Shop", "email": "shop@example.com"})
    vendor_id = create_resp.json()["id"]

    with patch("app.routers.vendor.stripe_service.create_account_link", return_value="https://connect.stripe.com/test"):
        resp = client.post(f"/api/vendors/{vendor_id}/onboard")
    assert resp.status_code == 200
    assert resp.json()["onboarding_url"] == "https://connect.stripe.com/test"


def test_get_vendor_status(client):
    mock_account = MagicMock()
    mock_account.id = "acct_status"
    with patch("app.routers.vendor.stripe_service.create_express_account", return_value=mock_account):
        create_resp = client.post("/api/vendors/", json={"business_name": "Status Co", "email": "status@example.com"})
    vendor_id = create_resp.json()["id"]

    resp = client.get(f"/api/vendors/{vendor_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == vendor_id


def test_get_vendor_not_found(client):
    import uuid
    resp = client.get(f"/api/vendors/{uuid.uuid4()}")
    assert resp.status_code == 404
