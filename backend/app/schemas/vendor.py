from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.vendor import OnboardingStatus


class VendorCreate(BaseModel):
    business_name: str
    email: EmailStr


class VendorOnboardResponse(BaseModel):
    onboarding_url: str


class VendorResponse(BaseModel):
    id: UUID
    business_name: str
    email: str
    stripe_account_id: Optional[str]
    onboarding_status: OnboardingStatus
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VendorListResponse(BaseModel):
    vendors: list[VendorResponse]
    total: int
