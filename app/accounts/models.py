from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.core.models import BaseModel

RoleEnum = ENUM(
    "learner",
    "instructor",
    "creator",
    "org_admin",
    "admin",
    "psychologist",
    "psychologist_pending",
    name="role_enum",
    create_type=True,
)


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False, index=True)
    phone_number = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(RoleEnum, nullable=False, default="learner")
    org_id = Column(PG_UUID(as_uuid=True), nullable=True)
    avatar = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    country = Column(String, nullable=True)
    xp = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    location = Column(String, nullable=True)

    # Relationships
    courses = relationship("Course", back_populates="creator",
                           foreign_keys="Course.created_by")
    enrollments = relationship("Enrollment", back_populates="user")
    progress_records = relationship("LessonProgress", back_populates="user")
    payments = relationship(
        "Payment", back_populates="user", foreign_keys="Payment.user_id")
    reviews = relationship("Review", back_populates="user")
    psychologist_profile = relationship(
        "PsychologistProfile", back_populates="user", uselist=False)
