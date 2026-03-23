from sqlalchemy import Column, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.models import BaseModel

PaymentProviderEnum = ENUM(
    "stripe", "flutterwave", "paystack",
    name="payment_provider_enum", create_type=True
)
PaymentStatusEnum = ENUM(
    "pending", "completed", "failed", "refunded",
    name="payment_status_enum", create_type=True
)
PayoutStatusEnum = ENUM(
    "pending", "processing", "completed", "failed",
    name="payout_status_enum", create_type=True
)


class Payment(BaseModel):
    __tablename__ = "payments"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(PG_UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True)
    org_id = Column(PG_UUID(as_uuid=True), nullable=True)
    amount = Column(Numeric, nullable=False)
    currency = Column(String, default="USD")
    provider = Column(PaymentProviderEnum, nullable=False)
    provider_txn_id = Column(String, nullable=True)
    status = Column(PaymentStatusEnum, nullable=False, default="pending")

    # Relationships
    user = relationship("User", back_populates="payments", foreign_keys=[user_id])
    course = relationship("Course", back_populates="payments", foreign_keys=[course_id])


class Payout(BaseModel):
    __tablename__ = "payouts"

    creator_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(PayoutStatusEnum, nullable=False, default="pending")
    payment_method = Column(String, nullable=False)
    payment_details = Column(JSONB, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)

