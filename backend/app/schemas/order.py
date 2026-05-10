from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.order import OrderStatus


class ChargeCreate(BaseModel):
    amount: int = Field(gt=0, description="Charge amount in cents (e.g. 10000 = $100.00)")


class OrderResponse(BaseModel):
    id: UUID
    vendor_id: UUID
    amount: int
    application_fee_amount: int
    idempotency_key: str
    status: OrderStatus
    stripe_payment_intent_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int
