from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.vendor import OnboardingStatus, Vendor
from app.schemas.vendor import VendorListResponse, VendorResponse
from app.services import stripe_service

router = APIRouter()


def require_admin(x_admin_key: str = Header(default="")):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key.")


@router.get("/vendors", response_model=VendorListResponse, dependencies=[Depends(require_admin)])
def list_vendors(db: Session = Depends(get_db)):
    vendors = db.query(Vendor).order_by(Vendor.created_at.desc()).all()
    return {"vendors": vendors, "total": len(vendors)}


@router.get("/vendors/{vendor_id}", response_model=VendorResponse, dependencies=[Depends(require_admin)])
def get_vendor(vendor_id: str, db: Session = Depends(get_db)):
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")
    return vendor


@router.post("/vendors/{vendor_id}/sync", response_model=VendorResponse, dependencies=[Depends(require_admin)])
def sync_vendor_status(vendor_id: str, db: Session = Depends(get_db)):
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")
    if not vendor.stripe_account_id:
        raise HTTPException(status_code=400, detail="Vendor has no Stripe account.")

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
    db.refresh(vendor)
    return vendor
