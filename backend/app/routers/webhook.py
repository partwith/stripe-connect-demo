from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.vendor import OnboardingStatus, Vendor
from app.services import stripe_service

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default="", alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    payload = await request.body()
    try:
        event = stripe_service.construct_webhook_event(payload, stripe_signature)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    if event.type == "account.updated":
        account = event.data.object
        vendor = db.query(Vendor).filter(Vendor.stripe_account_id == account.id).first()
        if vendor:
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

    return {"received": True}
