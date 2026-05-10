import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.vendor import Vendor, OnboardingStatus
from app.models.order import Order, OrderStatus
from app.config import settings

TEST_DB_URL = "sqlite:///./test_admin.db"
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


@pytest.fixture
def seeded_vendor():
    db = TestingSessionLocal()
    vendor_id = str(uuid.uuid4())
    vendor = Vendor(
        id=vendor_id,
        business_name="Seeded Corp",
        email="seeded@example.com",
        stripe_account_id="acct_seeded",
        onboarding_status=OnboardingStatus.COMPLETE,
        charges_enabled=True,
        payouts_enabled=True,
        details_submitted=True,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    db.close()
    return vendor


def test_list_vendors_requires_admin_key(client):
    resp = client.get("/api/admin/vendors")
    assert resp.status_code == 401


def test_list_vendors(client, seeded_vendor):
    resp = client.get("/api/admin/vendors", headers={"X-Admin-Key": ADMIN_KEY})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    emails = [v["email"] for v in data["vendors"]]
    assert "seeded@example.com" in emails


def test_get_vendor_detail(client, seeded_vendor):
    resp = client.get(
        f"/api/admin/vendors/{seeded_vendor.id}",
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["stripe_account_id"] == "acct_seeded"
    assert data["charges_enabled"] is True


def test_sync_vendor_status(client, seeded_vendor):
    mock_account = MagicMock()
    mock_account.charges_enabled = True
    mock_account.payouts_enabled = True
    mock_account.details_submitted = True
    with patch("app.routers.admin.stripe_service.get_account", return_value=mock_account):
        resp = client.post(
            f"/api/admin/vendors/{seeded_vendor.id}/sync",
            headers={"X-Admin-Key": ADMIN_KEY},
        )
    assert resp.status_code == 200
    assert resp.json()["charges_enabled"] is True
    assert resp.json()["onboarding_status"] == "complete"


def test_sync_updates_status_to_restricted(client, seeded_vendor):
    mock_account = MagicMock()
    mock_account.charges_enabled = False
    mock_account.payouts_enabled = False
    mock_account.details_submitted = False
    with patch("app.routers.admin.stripe_service.get_account", return_value=mock_account):
        resp = client.post(
            f"/api/admin/vendors/{seeded_vendor.id}/sync",
            headers={"X-Admin-Key": ADMIN_KEY},
        )
    assert resp.status_code == 200
    assert resp.json()["onboarding_status"] == "restricted"


def test_get_vendor_not_found(client):
    resp = client.get(
        f"/api/admin/vendors/{uuid.uuid4()}",
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert resp.status_code == 404


def test_create_charge_success(client, seeded_vendor):
    mock_pi = MagicMock()
    mock_pi.id = "pi_test_success"
    with patch("app.routers.admin.stripe_service.create_destination_charge", return_value=mock_pi):
        resp = client.post(
            f"/api/admin/vendors/{seeded_vendor.id}/charge",
            json={"amount": 10000},
            headers={"X-Admin-Key": ADMIN_KEY},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["amount"] == 10000
    assert data["application_fee_amount"] == 1000
    assert data["status"] == "processing"
    assert data["stripe_payment_intent_id"] == "pi_test_success"
    assert "idempotency_key" in data


def test_create_charge_requires_admin_key(client, seeded_vendor):
    resp = client.post(
        f"/api/admin/vendors/{seeded_vendor.id}/charge",
        json={"amount": 5000},
    )
    assert resp.status_code == 401


def test_create_charge_vendor_not_found(client):
    resp = client.post(
        f"/api/admin/vendors/{uuid.uuid4()}/charge",
        json={"amount": 5000},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert resp.status_code == 404


def test_create_charge_vendor_not_charges_enabled(client):
    db = TestingSessionLocal()
    vendor = Vendor(
        id=str(uuid.uuid4()),
        business_name="No Charges Corp",
        email="nocharge@example.com",
        stripe_account_id="acct_nopay",
        onboarding_status=OnboardingStatus.IN_PROGRESS,
        charges_enabled=False,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    vendor_id = vendor.id
    db.close()

    resp = client.post(
        f"/api/admin/vendors/{vendor_id}/charge",
        json={"amount": 5000},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert resp.status_code == 400


def test_create_charge_stripe_failure_marks_failed(client, seeded_vendor):
    with patch(
        "app.routers.admin.stripe_service.create_destination_charge",
        side_effect=Exception("card_declined"),
    ):
        resp = client.post(
            f"/api/admin/vendors/{seeded_vendor.id}/charge",
            json={"amount": 5000},
            headers={"X-Admin-Key": ADMIN_KEY},
        )
    assert resp.status_code == 400

    db = TestingSessionLocal()
    orders = db.query(Order).filter_by(vendor_id=seeded_vendor.id).all()
    assert len(orders) == 1
    assert orders[0].status == OrderStatus.FAILED
    db.close()


def test_list_orders(client, seeded_vendor):
    mock_pi = MagicMock()
    mock_pi.id = "pi_list_test"
    with patch("app.routers.admin.stripe_service.create_destination_charge", return_value=mock_pi):
        client.post(
            f"/api/admin/vendors/{seeded_vendor.id}/charge",
            json={"amount": 2000},
            headers={"X-Admin-Key": ADMIN_KEY},
        )

    resp = client.get(
        f"/api/admin/vendors/{seeded_vendor.id}/orders",
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["orders"][0]["amount"] == 2000
