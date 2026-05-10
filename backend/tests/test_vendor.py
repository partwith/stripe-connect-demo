from app.models.vendor import Vendor, OnboardingStatus


def test_vendor_model_fields():
    v = Vendor()
    assert hasattr(v, "id")
    assert hasattr(v, "business_name")
    assert hasattr(v, "email")
    assert hasattr(v, "stripe_account_id")
    assert hasattr(v, "onboarding_status")
    assert hasattr(v, "charges_enabled")
    assert hasattr(v, "payouts_enabled")
    assert hasattr(v, "details_submitted")
    assert hasattr(v, "created_at")
    assert hasattr(v, "updated_at")


def test_onboarding_status_values():
    assert OnboardingStatus.PENDING == "pending"
    assert OnboardingStatus.IN_PROGRESS == "in_progress"
    assert OnboardingStatus.COMPLETE == "complete"
    assert OnboardingStatus.RESTRICTED == "restricted"


from unittest.mock import patch, MagicMock
from app.services.stripe_service import (
    create_express_account,
    create_account_link,
    get_account,
    construct_webhook_event,
)


def test_create_express_account():
    mock_account = MagicMock()
    mock_account.id = "acct_test123"
    with patch(
        "app.services.stripe_service.stripe.Account.create",
        return_value=mock_account,
    ) as mock_create:
        result = create_express_account(email="vendor@example.com", business_name="Test Corp")
        mock_create.assert_called_once_with(
            type="express",
            email="vendor@example.com",
            business_profile={"name": "Test Corp"},
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
        )
        assert result.id == "acct_test123"


def test_create_account_link():
    mock_link = MagicMock()
    mock_link.url = "https://connect.stripe.com/setup/e/abc123"
    with patch(
        "app.services.stripe_service.stripe.AccountLink.create",
        return_value=mock_link,
    ):
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
    with patch(
        "app.services.stripe_service.stripe.Account.retrieve",
        return_value=mock_account,
    ):
        account = get_account("acct_test123")
        assert account.charges_enabled is True


def test_construct_webhook_event_invalid_raises():
    with patch(
        "app.services.stripe_service.stripe.Webhook.construct_event",
        side_effect=Exception("Invalid signature"),
    ):
        try:
            construct_webhook_event(b"{}", "bad_sig")
            assert False, "Should have raised"
        except Exception as e:
            assert "Invalid signature" in str(e)
