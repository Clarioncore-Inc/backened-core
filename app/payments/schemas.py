from typing import Any, Optional
from uuid import UUID
from datetime import datetime
from app.core.schema import BaseSchema


class PaymentCreate(BaseSchema):
    amount: float
    currency: str = "USD"
    provider: str
    course_id: Optional[UUID] = None
    org_id: Optional[UUID] = None


class PaymentUpdate(BaseSchema):
    status: str
    provider_txn_id: Optional[str] = None


class PaymentResponse(BaseSchema):
    id: UUID
    user_id: UUID
    course_id: Optional[UUID] = None
    org_id: Optional[UUID] = None
    amount: Any
    currency: str
    provider: str
    provider_txn_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class PayoutCreate(BaseSchema):
    amount: float
    currency: str
    payment_method: str
    payment_details: Optional[Any] = None


class PayoutResponse(BaseSchema):
    id: UUID
    creator_id: UUID
    amount: Any
    currency: str
    status: str
    payment_method: str
    payment_details: Optional[Any] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

