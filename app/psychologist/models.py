from sqlalchemy import Boolean, Column, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.models import BaseModel
from sqlalchemy.dialects.postgresql import ARRAY
from enum import Enum as PyEnum


InviteStatusEnum = ENUM(
    "pending", "accepted", "expired",
    name="invite_status_enum", create_type=True
)


PsychologistProfileEnum = ENUM(
    "pending", "approved", "rejected",
    name="psychologist_profile_enum", create_type=True
)


class BookingType(PyEnum):
    EMERGENCY = "emergency"
    STANDARD = "standard"


BookingTypeEnum = ENUM(
    *[e.value for e in BookingType],
    name="booking_type_enum", create_type=True
)


class PsychologistProfile(BaseModel):
    __tablename__ = "psychologist_profiles"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "users.id"), unique=True, nullable=False)
    hourly_rate = Column(Numeric, nullable=True)
    bio = Column(Text, nullable=True)
    license_number = Column(String, nullable=True)
    years_of_experience = Column(String, nullable=True)
    specialization = Column(Text, nullable=True)
    about_you = Column(Text, nullable=True)
    signature_image = Column(String, nullable=True)
    education_and_qualifications = Column(ARRAY(Text), nullable=True)
    certification_and_additional_training = Column(ARRAY(Text), nullable=True)
    default_session_duration = Column(Integer, nullable=True, default=60)
    default_booking_type = Column(BookingTypeEnum, nullable=True, default="standard")
    is_profile_public = Column(Boolean, nullable=False, default=True)
    accepting_new_clients = Column(Boolean, nullable=False, default=True)
    visible_profile_fields = Column(JSONB, nullable=True, default=dict)

    status = Column(
        PsychologistProfileEnum, nullable=True, default="pending")
    # Relationships
    user = relationship("User", back_populates="psychologist_profile")


class PsychologistInvite(BaseModel):
    __tablename__ = "psychologist_invites"

    email = Column(String, nullable=False)
    token = Column(String, nullable=False, unique=True)
    invited_by = Column(PG_UUID(as_uuid=True),
                        ForeignKey("users.id"), nullable=False)
    status = Column(InviteStatusEnum, nullable=False, default="pending")
    expires_at = Column(DateTime(timezone=True), nullable=False)


class RecurringFreq(PyEnum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


RecurringFreqEnum = ENUM(
    *[e.value for e in RecurringFreq],
    name="recurring_freq_enum", create_type=True
)


class BookingStatus(PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EMERGENCY = "emergency"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ACKNOWLEDGED = "acknowledged"


BookingStatusEnum = ENUM(
    *[e.value for e in BookingStatus],
    name="booking_status_enum", create_type=True
)


class Booking(BaseModel):
    __tablename__ = "bookings"

    student_id = Column(PG_UUID(as_uuid=True),
                        ForeignKey("users.id"), nullable=False)
    psychologist_id = Column(PG_UUID(as_uuid=True),
                             ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(String, nullable=False)
    session_type = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(BookingStatusEnum, nullable=False, default="pending")
    rejection_reason = Column(Text, nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurring_frequency = Column(RecurringFreqEnum, nullable=True)
    reminder_preferences = Column(JSONB, nullable=True)
    price = Column(Numeric, nullable=False)
    booking_type = Column(BookingTypeEnum, nullable=True, default="standard")
    session_notes = Column(JSONB, nullable=True)
    session_notes_updated_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("User", foreign_keys=[
                           student_id], back_populates="bookings_as_student")
    psychologist = relationship("User", foreign_keys=[
                                psychologist_id], back_populates="bookings_as_psychologist")

    model_config = {
        "from_attributes": True,
        "use_enum_values": True}


class AvailabilitySchedule(BaseModel):
    __tablename__ = "availability_schedules"

    psychologist_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "users.id"), nullable=False, unique=True)
    schedule = Column(JSONB, nullable=False, default=dict)

    psychologist = relationship("User", back_populates="availability_schedule")

    model_config = {
        "from_attributes": True,
        "use_enum_values": True
    }


class MeetingConfig(BaseModel):
    """Global meeting configuration — always one row (upsert pattern)."""
    __tablename__ = "meeting_config"

    name = Column(String, nullable=False)          # e.g. "Zoom", "Google Meet"
    link = Column(String, nullable=False)          # the meeting URL
    password = Column(String, nullable=True)       # optional password / passcode

    model_config = {
        "from_attributes": True,
        "use_enum_values": True
    }


class SessionType(BaseModel):
    __tablename__ = "session_types"

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric, nullable=False)
