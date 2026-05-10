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
