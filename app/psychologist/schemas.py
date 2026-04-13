from typing import Any, Optional
from uuid import UUID
from datetime import date, datetime
from app.core.schema import BaseSchema
from pydantic import EmailStr


class PsychologistProfileResponse(BaseSchema):
    id: UUID
    user_id: UUID
    hourly_rate: Optional[Any] = None
    bio: Optional[str] = None
    is_approved: bool
    created_at: datetime
    updated_at: datetime
    license_number: Optional[str] = None
    years_of_experience: Optional[str] = None
    specialization: Optional[str] = None
    about_you: Optional[str] = None
    location: Optional[str] = None
    education_and_qualifications: Optional[list[str]] = None
    certification_and_additional_training: Optional[list[str]] = None


class PsychologistProfileUpdate(BaseSchema):
    hourly_rate: Optional[float] = None
    bio: Optional[str] = None
    license_number: Optional[str] = None
    years_of_experience: Optional[str] = None
    specialization: Optional[str] = None
    about_you: Optional[str] = None
    location: Optional[str] = None
    education_and_qualifications: Optional[list[str]] = None
    certification_and_additional_training: Optional[list[str]] = None


class PsychologistRegisterCreate(BaseSchema):
    email: EmailStr
    full_name: str
    password: str
    hourly_rate: float
    bio: Optional[str] = None
    license_number: Optional[str] = None
    years_of_experience: Optional[str] = None
    specialization: Optional[str] = None
    about_you: Optional[str] = None
    location: Optional[str] = None
    education_and_qualifications: Optional[list[str]] = None
    certification_and_additional_training: Optional[list[str]] = None


class InviteCreate(BaseSchema):
    email: EmailStr


class InviteResponse(BaseSchema):
    id: UUID
    email: str
    status: str
    invited_by: UUID
    expires_at: datetime
    created_at: datetime


class AcceptInvitePayload(BaseSchema):
    token: str
    full_name: str
    password: str
    hourly_rate: float
    bio: Optional[str] = None
    license_number: Optional[str] = None
    years_of_experience: Optional[str] = None
    specialization: Optional[str] = None
    about_you: Optional[str] = None
    location: Optional[str] = None


class BookingCreate(BaseSchema):
    psychologist_id: UUID
    date: Optional[date] = None
    time: Optional[str] = None
    session_type: Optional[str] = None
    notes: Optional[str] = None
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None
    reminder_preferences: Optional[Any] = None
    price: Optional[float] = None


class BookingUpdate(BaseSchema):
    status: str


class BookingResponse(BaseSchema):
    id: UUID
    student_id: UUID
    psychologist_id: UUID
    date: Optional[date] = None
    time: str
    session_type: str
    notes: Optional[str] = None
    status: str
    is_recurring: bool
    recurring_frequency: Optional[str] = None
    reminder_preferences: Optional[Any] = None
    price: Optional[Any] = None
    created_at: datetime
    updated_at: datetime
