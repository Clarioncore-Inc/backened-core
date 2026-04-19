from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID as PG_UUID
from enum import Enum, StrEnum
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Table
from app.core.models import BaseModel
from app.database import Base


class LessonKind(StrEnum):
    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    INTERACTIVE = "interactive"
    PROBLEM = "problem"
    HEADING = "heading"
    IMAGE = "image"
    CODE = "code"
    HINT = "hint"
    CALLOUT = "callout"


LessonKindEnum = ENUM(
    *[e.value for e in LessonKind],
    name="lesson_kind_enum", create_type=True
)


section_attachments = Table(
    "section_attachments",
    Base.metadata,
    Column("section_id", PG_UUID(as_uuid=True),
           ForeignKey("sections.id"), primary_key=True),
    Column("attachment_id", PG_UUID(as_uuid=True),
           ForeignKey("attachments.id"), primary_key=True),
)


class Section(BaseModel):
    __tablename__ = "sections"

    title = Column(String, nullable=False)
    order = Column(Integer, default=0)
    course_id = Column(PG_UUID(as_uuid=True),
                       ForeignKey("courses.id"), nullable=False)
    url = Column(String, nullable=True)
    # attachment_id = Column(ForeignKey("attachments.id"), nullable=True)
    course = relationship("Course", back_populates="sections")
    duration = Column(Integer, default=0)

    lessons = relationship(
        "Lesson", back_populates="section", cascade="all, delete-orphan")

    attachments = relationship(
        "Attachment", secondary=section_attachments, back_populates="sections")


class LessonSettings(BaseModel):
    __abstract__ = True

    class DifficultyEnum(str, Enum):
        BEGINNER = "beginner"
        INTERMEDIATE = "intermediate"
        ADVANCED = "advanced"
    duration_minutes = Column(Integer, default=0)
    xp_reward = Column(Integer, default=0)
    difficulty = Column(ENUM(DifficultyEnum), nullable=True)


class Lesson(LessonSettings):
    __tablename__ = "lessons"

    section_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "sections.id"), nullable=False)
    title = Column(String, nullable=False)
    kind = Column(LessonKindEnum, nullable=False, default="text")
    content = Column(JSONB, nullable=True)
    position = Column(Integer, default=0)
    is_free = Column(Boolean, default=False)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    tag = Column(String, nullable=True)

    section = relationship("Section", back_populates="lessons")
    progress_records = relationship(
        "LessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    likes = relationship("LessonLike", back_populates="lesson",
                         cascade="all, delete-orphan")
    bookmarks = relationship(
        "LessonBookmark", back_populates="lesson", cascade="all, delete-orphan")
    comments = relationship(
        "LessonComment", back_populates="lesson", cascade="all, delete-orphan")

    video_content = relationship(
        "VideoLesson", back_populates="lesson", cascade="all, delete-orphan")
    text_content = relationship(
        "TextLesson", back_populates="lesson", cascade="all, delete-orphan")
    quiz_content = relationship(
        "QuizLesson", back_populates="lesson", cascade="all, delete-orphan")
    interactive_content = relationship(
        "InteractiveLesson", back_populates="lesson", cascade="all, delete-orphan")
    problem_content = relationship(
        "ProblemLesson", back_populates="lesson", cascade="all, delete-orphan")
    heading_content = relationship(
        "HeadingLesson", back_populates="lesson", cascade="all, delete-orphan")
    image_content = relationship(
        "ImageLesson", back_populates="lesson", cascade="all, delete-orphan")
    code_content = relationship(
        "CodeLesson", back_populates="lesson", cascade="all, delete-orphan")
    hint_content = relationship(
        "HintLesson", back_populates="lesson", cascade="all, delete-orphan")
    callout_content = relationship(
        "CalloutLesson", back_populates="lesson", cascade="all, delete-orphan")


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
