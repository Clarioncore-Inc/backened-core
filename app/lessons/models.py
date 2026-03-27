import uuid
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func
from app.core.models import BaseModel

LessonKindEnum = ENUM(
    "video", "interactive", "article", "quiz", "practice",
    name="lesson_kind_enum", create_type=True
)


class Section(BaseModel):
    __tablename__ = "sections"

    title = Column(String, nullable=False)
    order = Column(Integer, default=0)
    course_id = Column(PG_UUID(as_uuid=True),
                       ForeignKey("courses.id"), nullable=False)
    url = Column(String, nullable=True)
    course = relationship("Course", back_populates="sections")
    duration = Column(Integer, default=0)

    lessons = relationship(
        "Lesson", back_populates="section", cascade="all, delete-orphan")


class Lesson(BaseModel):
    __tablename__ = "lessons"

    section_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "sections.id"), nullable=False)
    title = Column(String, nullable=False)
    kind = Column(LessonKindEnum, nullable=False, default="article")
    content = Column(JSONB, nullable=True)
    position = Column(Integer, default=0)
    duration_minutes = Column(Integer, default=0)
    is_free = Column(Boolean, default=False)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    section = relationship("Section", back_populates="lessons")
    progress_records = relationship(
        "LessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    likes = relationship("LessonLike", back_populates="lesson",
                         cascade="all, delete-orphan")
    bookmarks = relationship(
        "LessonBookmark", back_populates="lesson", cascade="all, delete-orphan")
    comments = relationship(
        "LessonComment", back_populates="lesson", cascade="all, delete-orphan")


class LessonLike(BaseModel):
    __tablename__ = "lesson_likes"
    user_id = Column(PG_UUID(as_uuid=True),
                     ForeignKey("users.id"), nullable=False)
    lesson_id = Column(PG_UUID(as_uuid=True),
                       ForeignKey("lessons.id"), nullable=False)
    lesson = relationship("Lesson", back_populates="likes")


class LessonBookmark(BaseModel):
    __tablename__ = "lesson_bookmarks"
    user_id = Column(PG_UUID(as_uuid=True),
                     ForeignKey("users.id"), nullable=False)
    lesson_id = Column(PG_UUID(as_uuid=True),
                       ForeignKey("lessons.id"), nullable=False)
    lesson = relationship("Lesson", back_populates="bookmarks")


class LessonComment(BaseModel):
    __tablename__ = "lesson_comments"
    lesson_id = Column(PG_UUID(as_uuid=True),
                       ForeignKey("lessons.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True),
                     ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(PG_UUID(as_uuid=True), nullable=True)
    lesson = relationship("Lesson", back_populates="comments")
