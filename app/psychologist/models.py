from sqlalchemy import Boolean, Column, Date, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.models import BaseModel

BookingStatusEnum = ENUM(
    "confirmed", "emergency", "cancelled", "completed",
    name="booking_status_enum", create_type=True
)
RecurringFreqEnum = ENUM(
    "weekly", "biweekly", "monthly",
    name="recurring_freq_enum", create_type=True
)


class PsychologistProfile(BaseModel):
    __tablename__ = "psychologist_profiles"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    specialization = Column(String, nullable=False)
    hourly_rate = Column(Numeric, nullable=False)
    bio = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="psychologist_profile")


class Booking(BaseModel):
    __tablename__ = "bookings"

    student_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    psychologist_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(String, nullable=False)
    session_type = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(BookingStatusEnum, nullable=False, default="confirmed")
    is_recurring = Column(Boolean, default=False)
    recurring_frequency = Column(RecurringFreqEnum, nullable=True)
    reminder_preferences = Column(JSONB, nullable=True)
    price = Column(Numeric, nullable=False)

