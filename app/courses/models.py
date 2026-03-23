from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, Numeric, String, Text
)
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.models import BaseModel

LevelEnum = ENUM("beginner", "intermediate", "advanced", name="level_enum", create_type=True)
CourseStatusEnum = ENUM("draft", "published", "archived", name="course_status_enum", create_type=True)


class Course(BaseModel):
    __tablename__ = "courses"

    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    cover_image = Column(String, nullable=True)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=True)
    level = Column(LevelEnum, nullable=False, default="beginner")
    price = Column(Numeric, nullable=False, default=0)
    currency = Column(String, default="USD")
    is_public = Column(Boolean, default=True)
    status = Column(CourseStatusEnum, nullable=False, default="draft")
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    org_id = Column(PG_UUID(as_uuid=True), nullable=True)
    rating = Column(Float, default=0)
    total_reviews = Column(Integer, default=0)
    total_enrollments = Column(Integer, default=0)
    estimated_hours = Column(Float, default=0)
    tags = Column(ARRAY(String), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="courses", foreign_keys=[created_by])
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="course", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="course", foreign_keys="Payment.course_id")

