from sqlalchemy import Column, DateTime, Float
from sqlalchemy.dialects.postgresql import ENUM, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.models import BaseModel

EnrollmentStatusEnum = ENUM(
    "active", "completed", "dropped",
    name="enrollment_status_enum", create_type=True
)


class Enrollment(BaseModel):
    __tablename__ = "enrollments"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(PG_UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    status = Column(EnrollmentStatusEnum, nullable=False, default="active")
    progress = Column(Float, default=0)
    enrolled_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

