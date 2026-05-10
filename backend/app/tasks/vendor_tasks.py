from celery_worker import celery_app
from app.database import SessionLocal
from app.models.vendor import OnboardingStatus, Vendor
from app.services import stripe_service


@celery_app.task(name="app.tasks.vendor_tasks.sync_vendor_stripe_status")
def sync_vendor_stripe_status(vendor_id: str):
    db = SessionLocal()
    try:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor or not vendor.stripe_account_id:
            return
        account = stripe_service.get_account(vendor.stripe_account_id)
        vendor.charges_enabled = account.charges_enabled
        vendor.payouts_enabled = account.payouts_enabled
        vendor.details_submitted = account.details_submitted
        if account.charges_enabled and account.payouts_enabled:
            vendor.onboarding_status = OnboardingStatus.COMPLETE
        elif account.details_submitted:
            vendor.onboarding_status = OnboardingStatus.IN_PROGRESS
        else:
            vendor.onboarding_status = OnboardingStatus.RESTRICTED
        db.commit()
    finally:
        db.close()


@celery_app.task(name="app.tasks.vendor_tasks.sync_all_vendors")
def sync_all_vendors():
    db = SessionLocal()
    try:
        vendors = (
            db.query(Vendor)
            .filter(
                Vendor.stripe_account_id.isnot(None),
                Vendor.onboarding_status != OnboardingStatus.COMPLETE,
            )
            .all()
        )
        for vendor in vendors:
            sync_vendor_stripe_status.delay(str(vendor.id))
    finally:
        db.close()
