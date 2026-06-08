from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.schema import BaseSchema


class AppSettingsResponse(BaseSchema):
    id: UUID
    app_name: str
    logo: Optional[str] = None
    contacts: Optional[str] = None
    email: Optional[str] = None
    iq_test_price: float
    refresh_booking_in_minute: int
    psychologist_booking_reminder_in_minutes: int
    created_at: datetime
    updated_at: datetime


class AppSettingsUpdateRequest(BaseSchema):
    app_name: Optional[str] = None
    logo: Optional[str] = None
    contacts: Optional[str] = None
    email: Optional[str] = None
    iq_test_price: Optional[float] = None
    refresh_booking_in_minute: Optional[int] = None
    psychologist_booking_reminder_in_minutes: Optional[int] = None