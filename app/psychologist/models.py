from sqlalchemy import Boolean, Column, Date, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.models import BaseModel
from sqlalchemy.dialects.postgresql import ARRAY

BookingStatusEnum = ENUM(
    "confirmed", "emergency", "cancelled", "completed",
    name="booking_status_enum", create_type=True
)
RecurringFreqEnum = ENUM(
    "weekly", "biweekly", "monthly",
    name="recurring_freq_enum", create_type=True
)
InviteStatusEnum = ENUM(
    "pending", "accepted", "expired",
    name="invite_status_enum", create_type=True
)


class PsychologistProfile(BaseModel):
    __tablename__ = "psychologist_profiles"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "users.id"), unique=True, nullable=False)
    hourly_rate = Column(Numeric, nullable=False)
    bio = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False)
    license_number = Column(String, nullable=True)
    years_of_experience = Column(String, nullable=True)
    specialization = Column(Text, nullable=True)
    about_you = Column(Text, nullable=True)
    education_and_qualifications = Column(ARRAY(Text), nullable=True)
    certification_and_additional_training = Column(ARRAY(Text), nullable=True)
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
    status = Column(BookingStatusEnum, nullable=False, default="confirmed")
    is_recurring = Column(Boolean, default=False)
    recurring_frequency = Column(RecurringFreqEnum, nullable=True)
    reminder_preferences = Column(JSONB, nullable=True)
    price = Column(Numeric, nullable=False)
