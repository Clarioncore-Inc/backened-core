from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, Numeric, String, Text
)
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.models import BaseModel

LevelEnum = ENUM("beginner", "intermediate", "advanced", "all_levels",
                 name="level_enum", create_type=True)
CourseStatusEnum = ENUM("draft", "published", "archived",
                        name="course_status_enum", create_type=True)

CollaboratorRoleEnum = ENUM("co-instructor", "editor", "reviewer", "verifier",
                            name="collaborator_role_enum", create_type=True)


class CourseCollaborator(BaseModel):
    __tablename__ = "course_collaborators"

    course_id = Column(PG_UUID(as_uuid=True),
                       ForeignKey("courses.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True),
                     ForeignKey("users.id"), nullable=False)
    role = Column(CollaboratorRoleEnum, nullable=False,
                  default="co-instructor")

    course = relationship("Course", back_populates="collaborators")
    user = relationship("User")


class Course(BaseModel):
    __tablename__ = "courses"

    title = Column(String, nullable=False)
    sub_title = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    cover_image = Column(String, nullable=True)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=True)
    level = Column(LevelEnum, nullable=False, default="beginner")
    language = Column(String, nullable=True)
    price = Column(Numeric, nullable=False, default=0)
    discount = Column(Numeric, nullable=True)
    currency = Column(String, default="USD")
    is_public = Column(Boolean, default=True)
    status = Column(CourseStatusEnum, nullable=False, default="draft")
    created_by = Column(PG_UUID(as_uuid=True),
                        ForeignKey("users.id"), nullable=False)
    org_id = Column(PG_UUID(as_uuid=True), nullable=True)
    rating = Column(Float, default=0)
    total_reviews = Column(Integer, default=0)
    total_enrollments = Column(Integer, default=0)
    estimated_hours = Column(Float, default=0)
    tags = Column(ARRAY(String), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    thubnail = Column(String, nullable=True)

    course_goals = Column(ARRAY(String), nullable=True)
    learning_objectives = Column(ARRAY(String), nullable=True)
    prerequisites = Column(ARRAY(String), nullable=True)
    who_this_course_is_for = Column(String, nullable=True)

    enable_discussions = Column(Boolean, default=True)
    enable_reviews = Column(Boolean, default=True)
    enable_certificates = Column(Boolean, default=False)
    maximum_students = Column(Integer, nullable=True)

    creator = relationship(
        "User", back_populates="courses", foreign_keys=[created_by])
    sections = relationship(
        "Section", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan")
    reviews = relationship(
        "Review", back_populates="course", cascade="all, delete-orphan")
    payments = relationship(
        "Payment", back_populates="course", foreign_keys="Payment.course_id")
    collaborators = relationship(
        "CourseCollaborator", back_populates="course", cascade="all, delete-orphan")
