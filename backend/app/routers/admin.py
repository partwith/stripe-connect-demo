import uuid as _uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.vendor import OnboardingStatus, Vendor
from app.schemas.order import ChargeCreate, OrderListResponse, OrderResponse
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


@router.post("/vendors/{vendor_id}/charge", response_model=OrderResponse, dependencies=[Depends(require_admin)])
def create_charge(vendor_id: str, body: ChargeCreate, db: Session = Depends(get_db)):
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")
    if not vendor.stripe_account_id:
        raise HTTPException(status_code=400, detail="Vendor has no Stripe account.")
    if not vendor.charges_enabled:
        raise HTTPException(status_code=400, detail="Vendor charges are not enabled.")

    idempotency_key = str(_uuid.uuid4())
    application_fee_amount = int(body.amount * 0.10)

    order = Order(
        vendor_id=vendor_id,
        amount=body.amount,
        application_fee_amount=application_fee_amount,
        idempotency_key=idempotency_key,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    db.flush()

    try:
        pi = stripe_service.create_destination_charge(
            amount=body.amount,
            application_fee_amount=application_fee_amount,
            destination_account=vendor.stripe_account_id,
            idempotency_key=idempotency_key,
        )
        order.stripe_payment_intent_id = pi.id
        order.status = OrderStatus.PROCESSING
    except Exception as exc:
        order.status = OrderStatus.FAILED
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc))

    db.commit()
    db.refresh(order)
    return order


@router.get("/vendors/{vendor_id}/orders", response_model=OrderListResponse, dependencies=[Depends(require_admin)])
def list_orders(vendor_id: str, db: Session = Depends(get_db)):
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")
    orders = (
        db.query(Order)
        .filter(Order.vendor_id == vendor_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return {"orders": orders, "total": len(orders)}
