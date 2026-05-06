from sqlalchemy import Boolean, Column, Date, DateTime, Numeric, String, Text
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
    CONFIRMED = "confirmed"
    EMERGENCY = "emergency"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


BookingStatusEnum = ENUM(
    *[e.value for e in BookingStatus],
    name="booking_status_enum", create_type=True
)


class BookingType(PyEnum):
    EMERGENCY = "emergency"
    STANDARD = "standard"


BookingTypeEnum = ENUM(
    *[e.value for e in BookingType],
    name="booking_type_enum", create_type=True
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
    status = Column(BookingStatusEnum, nullable=False, default="confirmed")
    is_recurring = Column(Boolean, default=False)
    recurring_frequency = Column(RecurringFreqEnum, nullable=True)
    reminder_preferences = Column(JSONB, nullable=True)
    price = Column(Numeric, nullable=False)
    booking_type = Column(BookingTypeEnum, nullable=True, default="standard")

    student = relationship("User", foreign_keys=[
                           student_id], back_populates="bookings_as_student")
    psychologist = relationship("User", foreign_keys=[
                                psychologist_id], back_populates="bookings_as_psychologist")

    model_config = {
        "from_attributes": True,
        "use_enum_values": True}
