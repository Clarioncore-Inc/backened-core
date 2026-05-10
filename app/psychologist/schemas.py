import json

from pydantic import computed_field, field_validator, model_validator
from typing import Any, Optional
from uuid import UUID
from datetime import date, datetime
from app.core.schema import BaseSchema
from pydantic import EmailStr
from app.accounts.schemas import UserResponse, UserUpdate
from enum import Enum
from app.psychologist.models import BookingType, BookingStatus, RecurringFreq


class PsychologistProfileStatus(Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = "rejected"


class SessionPlatform(Enum):
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    OTHER = "other"


class VisibleProfileFields(BaseSchema):
    bio: bool = True
    location: bool = True
    phone_number: bool = False
    hourly_rate: bool = True


class PsychologistProfileResponse(BaseSchema):
    id: UUID
    user:   Optional[UserResponse] = None
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
    status: Optional[PsychologistProfileStatus] = None
    default_session_duration: Optional[int] = None
    default_booking_type: Optional[BookingType] = None
    allow_emergency_bookings: Optional[bool] = None
    is_profile_public: Optional[bool] = None
    accepting_new_clients: Optional[bool] = None
    visible_profile_fields: Optional[VisibleProfileFields] = None


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
    status: Optional[PsychologistProfileStatus] = None
    user: Optional[UserUpdate] = None
    default_session_duration: Optional[int] = None
    default_booking_type: Optional[BookingType] = None
    allow_emergency_bookings: Optional[bool] = None
    is_profile_public: Optional[bool] = None
    accepting_new_clients: Optional[bool] = None
    visible_profile_fields: Optional[VisibleProfileFields] = None

    @field_validator("default_session_duration")
    @classmethod
    def validate_default_session_duration(cls, value: Optional[int]):
        if value is not None and value <= 0:
            raise ValueError("default_session_duration must be greater than 0")
        return value

    # model_config = {"from_attributes": True,
    #                 "use_enum_values": True}


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
    status: Optional[PsychologistProfileStatus] = None
    default_session_duration: Optional[int] = 60
    default_booking_type: Optional[BookingType] = BookingType.STANDARD
    allow_emergency_bookings: bool = False
    is_profile_public: bool = True
    accepting_new_clients: bool = True
    visible_profile_fields: Optional[VisibleProfileFields] = None


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
    default_session_duration: Optional[int] = 60
    default_booking_type: Optional[BookingType] = BookingType.STANDARD
    allow_emergency_bookings: bool = False
    is_profile_public: bool = True
    accepting_new_clients: bool = True
    visible_profile_fields: Optional[VisibleProfileFields] = None


class BookingCreate(BaseSchema):
    psychologist_id: UUID
    date: date
    time: Optional[str] = None
    session_type: Optional[str] = None
    notes: Optional[str] = None
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None
    reminder_preferences: Optional[Any] = None
    price: Optional[float] = None
    booking_type: Optional[BookingType] = None
    status: Optional[BookingStatus] = None

    model_config = {"from_attributes": True,
                    "use_enum_values": True}

    @field_validator("recurring_frequency", mode="before")
    @classmethod
    def normalize_recurring_frequency(cls, value: Any):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return value

    @field_validator("reminder_preferences", mode="before")
    @classmethod
    def normalize_reminder_preferences(cls, value: Any):
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None

            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return value

            if isinstance(parsed, str):
                parsed = parsed.strip()
                if not parsed:
                    return None
                try:
                    return json.loads(parsed)
                except json.JSONDecodeError:
                    return parsed

            return parsed

        return value

    @model_validator(mode="after")
    def clear_non_recurring_frequency(self):
        if not self.is_recurring:
            self.recurring_frequency = None
        return self


class BookingTransitionPayload(BaseSchema):
    status: BookingStatus
    rejection_reason: Optional[str] = None

    @field_validator("rejection_reason", mode="before")
    @classmethod
    def normalize_rejection_reason(cls, value: Any):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return value

    @model_validator(mode="after")
    def validate_transition(self):
        allowed_statuses = {
            BookingStatus.CONFIRMED,
            BookingStatus.CANCELLED,
            BookingStatus.COMPLETED,
        }
        if self.status not in allowed_statuses:
            raise ValueError(
                "Booking status transitions only support confirmed, cancelled, or completed"
            )

        if self.status == BookingStatus.CANCELLED and not self.rejection_reason:
            raise ValueError("Rejection reason is required when rejecting a booking")

        return self


class BookingResponse(BaseSchema):
    id: UUID
    psychologist: Optional[UserResponse] = None
    student: Optional[UserResponse] = None
    date: date
    time: str
    session_type: str
    notes: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    is_recurring: bool
    recurring_frequency: Optional[RecurringFreq] = None
    reminder_preferences: Optional[Any] = None
    price: Optional[Any] = None
    created_at: datetime
    updated_at: datetime
    booking_type: Optional[BookingType] = None
    session_notes: Optional[Any] = None
    session_notes_updated_at: Optional[datetime] = None


class BookingNotesPayload(BaseSchema):
    meeting_platform: Optional[SessionPlatform] = None
    meeting_link: Optional[str] = None
    session_summary: Optional[str] = None
    presenting_concerns: Optional[str] = None
    observations: Optional[str] = None
    interventions_used: Optional[list[str]] = None
    risk_assessment: Optional[str] = None
    homework_assigned: Optional[str] = None
    follow_up_plan: Optional[str] = None
    next_session_focus: Optional[str] = None
    private_notes: Optional[str] = None
    next_session_recommended: Optional[bool] = None

    @field_validator(
        "meeting_link",
        "session_summary",
        "presenting_concerns",
        "observations",
        "risk_assessment",
        "homework_assigned",
        "follow_up_plan",
        "next_session_focus",
        "private_notes",
        mode="before",
    )
    @classmethod
    def normalize_optional_strings(cls, value: Any):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return value


class BookingNotesResponse(BookingNotesPayload):
    updated_at: Optional[datetime] = None


class DaySchedule(BaseSchema):
    enabled: bool = True
    start: str = "10:00"
    end: str = "18:00"


class AvailabilityScheduleCreate(BaseSchema):
    monday: DaySchedule = DaySchedule()
    tuesday: DaySchedule = DaySchedule()
    wednesday: DaySchedule = DaySchedule()
    thursday: DaySchedule = DaySchedule()
    friday: DaySchedule = DaySchedule()
    saturday: DaySchedule = DaySchedule()
    sunday: DaySchedule = DaySchedule()


class AvailabilityScheduleResponse(BaseSchema):
    id: UUID
    psychologist_id: UUID
    schedule: AvailabilityScheduleCreate
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def working_days(self) -> int:
        return sum(1 for day in self.schedule.model_dump().values() if day["enabled"])

    @computed_field
    @property
    def total_hours(self) -> float:
        total = 0.0
        for day in self.schedule.model_dump().values():
            if day["enabled"]:
                start = datetime.strptime(day["start"], "%H:%M")
                end = datetime.strptime(day["end"], "%H:%M")
                total += (end - start).seconds / 3600
        return total
