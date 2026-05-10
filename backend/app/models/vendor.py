import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class OnboardingStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    RESTRICTED = "restricted"


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    stripe_account_id = Column(String(255), nullable=True, unique=True)
    onboarding_status = Column(
        Enum(OnboardingStatus, values_callable=lambda x: [e.value for e in x]),
        default=OnboardingStatus.PENDING,
        nullable=False,
    )
    charges_enabled = Column(Boolean, default=False, nullable=False)
    payouts_enabled = Column(Boolean, default=False, nullable=False)
    details_submitted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
