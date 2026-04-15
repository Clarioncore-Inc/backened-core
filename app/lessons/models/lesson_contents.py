from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.models import BaseModel


LessonKindEnum = ENUM(
    "video", "text", "quiz", "interactive", "problem",
    "heading", "image", "code", "hint", "callout",
    name="lesson_kind_enum", create_type=True
)


CalloutTypeEnum = ENUM(
    "info", "warning", "danger", "success",
    name="callout_type_enum", create_type=True
)


# ---------------------------------------------------------------------------
# Video Lesson
# ---------------------------------------------------------------------------
class VideoLesson(BaseModel):
    __tablename__ = "video_lessons"

    lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "lessons.id"), nullable=False)

    video_id = Column(ForeignKey("attachments.id"),
                      nullable=True)   # uploaded to S3
    # YouTube / Vimeo etc.
    external_url = Column(String, nullable=True)
    duration_seconds = Column(Integer, default=0)
    thumbnail_id = Column(ForeignKey("attachments.id"), nullable=True)
    transcript = Column(Text, nullable=True)
    subtitles_id = Column(ForeignKey("attachments.id"),
                          nullable=True)  # .vtt / .srt file
    allow_download = Column(Boolean, default=False)

    lesson = relationship("Lesson", back_populates="video_content")
    video = relationship("Attachment", foreign_keys=[video_id])
    thumbnail = relationship("Attachment", foreign_keys=[thumbnail_id])
    subtitles = relationship("Attachment", foreign_keys=[subtitles_id])


# ---------------------------------------------------------------------------
# Text Lesson
# ---------------------------------------------------------------------------
class TextLesson(BaseModel):
    __tablename__ = "text_lessons"

    lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "lessons.id"), nullable=False)

    body = Column(Text, nullable=False)           # rich-text / markdown / HTML
    estimated_read_minutes = Column(Integer, default=0)

    lesson = relationship("Lesson", back_populates="text_content")
    attachments = relationship(
        "TextLessonAttachment", back_populates="text_lesson", cascade="all, delete-orphan")


class TextLessonAttachment(BaseModel):
    """Extra files (PDFs, images) embedded inside a text lesson."""
    __tablename__ = "text_lesson_attachments"

    text_lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "text_lessons.id"), nullable=False)
    attachment_id = Column(ForeignKey("attachments.id"), nullable=False)

    text_lesson = relationship("TextLesson", back_populates="attachments")
    attachment = relationship("Attachment")


# ---------------------------------------------------------------------------
# Quiz Lesson
# ---------------------------------------------------------------------------
QuestionTypeEnum = ENUM(
    "single_choice", "multiple_choice", "true_false", "short_answer",
    name="question_type_enum", create_type=True
)


class QuizLesson(BaseModel):
    __tablename__ = "quiz_lessons"

    lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "lessons.id"), nullable=False)

    passing_score = Column(Integer, default=70)       # percentage
    max_attempts = Column(Integer, nullable=True)     # None = unlimited
    time_limit_minutes = Column(Integer, nullable=True)
    shuffle_questions = Column(Boolean, default=False)
    show_correct_answers = Column(Boolean, default=True)

    lesson = relationship("Lesson", back_populates="quiz_content")
    questions = relationship(
        "QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(BaseModel):
    __tablename__ = "quiz_questions"

    quiz_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "quiz_lessons.id"), nullable=False)
    question_type = Column(
        QuestionTypeEnum, nullable=False, default="single_choice")
    text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)          # shown after answering
    image_id = Column(ForeignKey("attachments.id"), nullable=True)
    position = Column(Integer, default=0)
    points = Column(Integer, default=1)

    quiz = relationship("QuizLesson", back_populates="questions")
    image = relationship("Attachment")
    options = relationship(
        "QuizQuestionOption", back_populates="question", cascade="all, delete-orphan")


class QuizQuestionOption(BaseModel):
    __tablename__ = "quiz_question_options"

    question_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "quiz_questions.id"), nullable=False)
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    position = Column(Integer, default=0)

    question = relationship("QuizQuestion", back_populates="options")


# ---------------------------------------------------------------------------
# Interactive Lesson  (step-based, e.g. drag-drop, fill-blanks, coding tasks)
# ---------------------------------------------------------------------------
InteractiveStepTypeEnum = ENUM(
    "instruction", "fill_blank", "drag_drop", "matching",
    "code_challenge", "image_hotspot", "sorting",
    name="interactive_step_type_enum", create_type=True
)


class InteractiveLesson(BaseModel):
    __tablename__ = "interactive_lessons"

    lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "lessons.id"), nullable=False)
    passing_score = Column(Integer, default=70)

    lesson = relationship("Lesson", back_populates="interactive_content")
    steps = relationship(
        "InteractiveStep", back_populates="interactive_lesson", cascade="all, delete-orphan")


class InteractiveStep(BaseModel):
    __tablename__ = "interactive_steps"

    interactive_lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "interactive_lessons.id"), nullable=False)
    step_type = Column(InteractiveStepTypeEnum, nullable=False)
    title = Column(String, nullable=True)
    instructions = Column(Text, nullable=True)
    position = Column(Integer, default=0)
    # Flexible payload: stores question data, correct answers, config per step type
    payload = Column(JSONB, nullable=False, default=dict)
    image_id = Column(ForeignKey("attachments.id"), nullable=True)
    points = Column(Integer, default=1)

    interactive_lesson = relationship(
        "InteractiveLesson", back_populates="steps")
    image = relationship("Attachment")


# ---------------------------------------------------------------------------
# Problem Lesson  (coding / math problem with test cases)
# ---------------------------------------------------------------------------
DifficultyEnum = ENUM(
    "easy", "medium", "hard",
    name="difficulty_enum", create_type=True
)


class ProblemLesson(BaseModel):
    __tablename__ = "problem_lessons"

    lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "lessons.id"), nullable=False)

    # problem description (markdown)
    statement = Column(Text, nullable=False)
    difficulty = Column(DifficultyEnum, default="medium")
    # boilerplate given to student
    starter_code = Column(Text, nullable=True)
    # hidden reference solution
    solution_code = Column(Text, nullable=True)
    # e.g. "python", "javascript"
    language = Column(String, nullable=True)
    time_limit_seconds = Column(Integer, default=5)
    memory_limit_mb = Column(Integer, default=256)
    hints = Column(ARRAY(String), nullable=True)
    image_id = Column(ForeignKey("attachments.id"), nullable=True)

    lesson = relationship("Lesson", back_populates="problem_content")
    image = relationship("Attachment")
    test_cases = relationship(
        "ProblemTestCase", back_populates="problem", cascade="all, delete-orphan")


class ProblemTestCase(BaseModel):
    __tablename__ = "problem_test_cases"

    problem_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "problem_lessons.id"), nullable=False)
    input = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    is_sample = Column(Boolean, default=False)   # visible to student vs hidden
    position = Column(Integer, default=0)

    problem = relationship("ProblemLesson", back_populates="test_cases")


# ---------------------------------------------------------------------------
# Heading Lesson
# ---------------------------------------------------------------------------
class HeadingLesson(BaseModel):
    __tablename__ = "heading_lessons"

    lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "lessons.id"), nullable=False)
    text = Column(String, nullable=False)
    level = Column(Integer, default=1)

    lesson = relationship("Lesson", back_populates="heading_content")


# ---------------------------------------------------------------------------
# Image Lesson
# ---------------------------------------------------------------------------
class ImageLesson(BaseModel):
    __tablename__ = "image_lessons"

    lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "lessons.id"), nullable=False)
    image_id = Column(ForeignKey("attachments.id"), nullable=False)
    caption = Column(String, nullable=True)
    alt_text = Column(String, nullable=True)

    lesson = relationship("Lesson", back_populates="image_content")
    image = relationship("Attachment", foreign_keys=[image_id])


# ---------------------------------------------------------------------------
# Code Lesson
# ---------------------------------------------------------------------------
class CodeLesson(BaseModel):
    __tablename__ = "code_lessons"

    lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "lessons.id"), nullable=False)
    code = Column(Text, nullable=False)
    language = Column(String, nullable=True)
    filename = Column(String, nullable=True)
    show_line_numbers = Column(Boolean, default=True)

    lesson = relationship("Lesson", back_populates="code_content")


# ---------------------------------------------------------------------------
# Hint Lesson
# ---------------------------------------------------------------------------
class HintLesson(BaseModel):
    __tablename__ = "hint_lessons"

    lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "lessons.id"), nullable=False)
    text = Column(Text, nullable=False)
    is_collapsible = Column(Boolean, default=True)

    lesson = relationship("Lesson", back_populates="hint_content")


# ---------------------------------------------------------------------------
# Callout Lesson
# ---------------------------------------------------------------------------
class CalloutLesson(BaseModel):
    __tablename__ = "callout_lessons"

    lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "lessons.id"), nullable=False)
    text = Column(Text, nullable=False)
    callout_type = Column(CalloutTypeEnum, default="info")
    title = Column(String, nullable=True)

    lesson = relationship("Lesson", back_populates="callout_content")
