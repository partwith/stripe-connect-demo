from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.vendor import OnboardingStatus, Vendor
from app.schemas.vendor import VendorCreate, VendorOnboardResponse, VendorPublicResponse, VendorResponse
from app.services import stripe_service

router = APIRouter()


@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def register_vendor(payload: VendorCreate, db: Session = Depends(get_db)):
    account = stripe_service.create_express_account(
        email=payload.email, business_name=payload.business_name
    )
    vendor = Vendor(
        business_name=payload.business_name,
        email=payload.email,
        stripe_account_id=account.id,
    )
    db.add(vendor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A vendor with this email already exists.")
    db.refresh(vendor)
    return vendor


@router.post("/{vendor_id}/onboard", response_model=VendorOnboardResponse)
def create_onboard_link(vendor_id: UUID, request: Request, db: Session = Depends(get_db)):
    vendor = db.get(Vendor, str(vendor_id))
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")

    api_base = str(request.base_url).rstrip("/")
    return_url = f"{settings.frontend_url}/return?vendor_id={vendor_id}"
    refresh_url = f"{api_base}/api/vendors/{vendor_id}/onboard"

    url = stripe_service.create_account_link(
        account_id=vendor.stripe_account_id,
        return_url=return_url,
        refresh_url=refresh_url,
    )
    vendor.onboarding_status = OnboardingStatus.IN_PROGRESS
    db.commit()
    return {"onboarding_url": url}


@router.get("/{vendor_id}", response_model=VendorPublicResponse)
def get_vendor(vendor_id: UUID, db: Session = Depends(get_db)):
    vendor = db.get(Vendor, str(vendor_id))
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")
    return vendor
