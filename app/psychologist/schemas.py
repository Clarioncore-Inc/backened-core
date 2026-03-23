from typing import Any, Optional
from uuid import UUID
from datetime import date, datetime
from app.core.schema import BaseSchema


class PsychologistProfileResponse(BaseSchema):
    id: UUID
    user_id: UUID
    specialization: str
    hourly_rate: Any
    bio: Optional[str] = None
    is_approved: bool
    created_at: datetime
    updated_at: datetime


class BookingCreate(BaseSchema):
    psychologist_id: UUID
    date: date
    time: str
    session_type: str
    notes: Optional[str] = None
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None
    reminder_preferences: Optional[Any] = None
    price: float


class BookingUpdate(BaseSchema):
    status: str


class BookingResponse(BaseSchema):
    id: UUID
    student_id: UUID
    psychologist_id: UUID
    date: date
    time: str
    session_type: str
    notes: Optional[str] = None
    status: str
    is_recurring: bool
    recurring_frequency: Optional[str] = None
    reminder_preferences: Optional[Any] = None
    price: Any
    created_at: datetime
    updated_at: datetime

