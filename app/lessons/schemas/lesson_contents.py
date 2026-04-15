from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import model_validator
from app.core.schema import BaseSchema
from app.attachment.schemas import AttachmentResponse


class LessonContentSchema(BaseSchema):
    @model_validator(mode="before")
    @classmethod
    def normalize_empty_uuid_values(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        uuid_field_names = {"video_id", "thumbnail_id", "subtitles_id", "image_id"}
        uuid_list_field_names = {"attachment_ids"}

        normalized = dict(data)
        for field_name in uuid_field_names:
            value = normalized.get(field_name)
            if isinstance(value, str) and not value.strip():
                normalized[field_name] = None

        for field_name in uuid_list_field_names:
            value = normalized.get(field_name)
            if isinstance(value, str) and not value.strip():
                normalized[field_name] = None
            elif isinstance(value, list):
                cleaned_values = [
                    item for item in value
                    if not (isinstance(item, str) and not item.strip())
                ]
                normalized[field_name] = cleaned_values

        return normalized


# ---------------------------------------------------------------------------
# Video
# ---------------------------------------------------------------------------
class VideoLessonCreate(LessonContentSchema):
    lesson_id: UUID
    video_id: Optional[UUID] = None
    external_url: Optional[str] = None
    duration_seconds: int = 0
    thumbnail_id: Optional[UUID] = None
    transcript: Optional[str] = None
    subtitles_id: Optional[UUID] = None
    allow_download: bool = False


class VideoLessonUpdate(LessonContentSchema):
    video_id: Optional[UUID] = None
    external_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    thumbnail_id: Optional[UUID] = None
    transcript: Optional[str] = None
    subtitles_id: Optional[UUID] = None
    allow_download: Optional[bool] = None


class VideoLessonResponse(LessonContentSchema):
    id: UUID
    lesson_id: UUID
    video_id: Optional[UUID] = None
    external_url: Optional[str] = None
    duration_seconds: int
    thumbnail_id: Optional[UUID] = None
    transcript: Optional[str] = None
    subtitles_id: Optional[UUID] = None
    allow_download: bool
    video: Optional[AttachmentResponse] = None
    thumbnail: Optional[AttachmentResponse] = None
    subtitles: Optional[AttachmentResponse] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------
class TextLessonAttachmentResponse(LessonContentSchema):
    id: UUID
    attachment: AttachmentResponse


class TextLessonCreate(LessonContentSchema):
    lesson_id: UUID
    body: str
    estimated_read_minutes: int = 0
    attachment_ids: Optional[List[UUID]] = None


class TextLessonUpdate(LessonContentSchema):
    body: Optional[str] = None
    estimated_read_minutes: Optional[int] = None
    attachment_ids: Optional[List[UUID]] = None


class TextLessonResponse(LessonContentSchema):
    id: UUID
    lesson_id: UUID
    body: str
    estimated_read_minutes: int
    attachments: List[TextLessonAttachmentResponse] = []
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------
class QuizQuestionOptionCreate(LessonContentSchema):
    text: str
    is_correct: bool = False
    position: int = 0


class QuizQuestionOptionUpdate(LessonContentSchema):
    text: Optional[str] = None
    is_correct: Optional[bool] = None
    position: Optional[int] = None


class QuizQuestionOptionResponse(LessonContentSchema):
    id: UUID
    text: str
    is_correct: bool
    position: int


class QuizQuestionCreate(LessonContentSchema):
    question_type: str = "single_choice"
    text: str
    explanation: Optional[str] = None
    image_id: Optional[UUID] = None
    position: int = 0
    points: int = 1
    options: List[QuizQuestionOptionCreate] = []


class QuizQuestionUpdate(LessonContentSchema):
    question_type: Optional[str] = None
    text: Optional[str] = None
    explanation: Optional[str] = None
    image_id: Optional[UUID] = None
    position: Optional[int] = None
    points: Optional[int] = None
    options: Optional[List[QuizQuestionOptionCreate]] = None


class QuizQuestionResponse(LessonContentSchema):
    id: UUID
    quiz_id: UUID
    question_type: str
    text: str
    explanation: Optional[str] = None
    image_id: Optional[UUID] = None
    position: int
    points: int
    image: Optional[AttachmentResponse] = None
    options: List[QuizQuestionOptionResponse] = []


class QuizLessonCreate(LessonContentSchema):
    lesson_id: UUID
    passing_score: int = 70
    max_attempts: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    shuffle_questions: bool = False
    show_correct_answers: bool = True
    questions: List[QuizQuestionCreate] = []


class QuizLessonUpdate(LessonContentSchema):
    passing_score: Optional[int] = None
    max_attempts: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    shuffle_questions: Optional[bool] = None
    show_correct_answers: Optional[bool] = None
    questions: Optional[List[QuizQuestionCreate]] = None


class QuizLessonResponse(LessonContentSchema):
    id: UUID
    lesson_id: UUID
    passing_score: int
    max_attempts: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    shuffle_questions: bool
    show_correct_answers: bool
    questions: List[QuizQuestionResponse] = []
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Interactive
# ---------------------------------------------------------------------------
class InteractiveStepCreate(LessonContentSchema):
    step_type: str
    title: Optional[str] = None
    instructions: Optional[str] = None
    position: int = 0
    payload: Dict[str, Any] = {}
    image_id: Optional[UUID] = None
    points: int = 1


class InteractiveStepUpdate(LessonContentSchema):
    step_type: Optional[str] = None
    title: Optional[str] = None
    instructions: Optional[str] = None
    position: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None
    image_id: Optional[UUID] = None
    points: Optional[int] = None


class InteractiveStepResponse(LessonContentSchema):
    id: UUID
    interactive_lesson_id: UUID
    step_type: str
    title: Optional[str] = None
    instructions: Optional[str] = None
    position: int
    payload: Dict[str, Any]
    image_id: Optional[UUID] = None
    points: int
    image: Optional[AttachmentResponse] = None


class InteractiveLessonCreate(LessonContentSchema):
    lesson_id: UUID
    passing_score: int = 70
    steps: List[InteractiveStepCreate] = []


class InteractiveLessonUpdate(LessonContentSchema):
    passing_score: Optional[int] = None
    steps: Optional[List[InteractiveStepCreate]] = None


class InteractiveLessonResponse(LessonContentSchema):
    id: UUID
    lesson_id: UUID
    passing_score: int
    steps: List[InteractiveStepResponse] = []
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Problem
# ---------------------------------------------------------------------------
class ProblemTestCaseCreate(LessonContentSchema):
    input: str
    expected_output: str
    is_sample: bool = False
    position: int = 0


class ProblemTestCaseUpdate(LessonContentSchema):
    input: Optional[str] = None
    expected_output: Optional[str] = None
    is_sample: Optional[bool] = None
    position: Optional[int] = None


class ProblemTestCaseResponse(LessonContentSchema):
    id: UUID
    input: str
    expected_output: str
    is_sample: bool
    position: int


class ProblemLessonCreate(LessonContentSchema):
    lesson_id: UUID
    statement: str
    difficulty: str = "medium"
    starter_code: Optional[str] = None
    solution_code: Optional[str] = None
    language: Optional[str] = None
    time_limit_seconds: int = 5
    memory_limit_mb: int = 256
    hints: Optional[List[str]] = None
    image_id: Optional[UUID] = None
    test_cases: List[ProblemTestCaseCreate] = []


class ProblemLessonUpdate(LessonContentSchema):
    statement: Optional[str] = None
    difficulty: Optional[str] = None
    starter_code: Optional[str] = None
    solution_code: Optional[str] = None
    language: Optional[str] = None
    time_limit_seconds: Optional[int] = None
    memory_limit_mb: Optional[int] = None
    hints: Optional[List[str]] = None
    image_id: Optional[UUID] = None
    test_cases: Optional[List[ProblemTestCaseCreate]] = None


class ProblemLessonResponse(LessonContentSchema):
    id: UUID
    lesson_id: UUID
    statement: str
    difficulty: str
    starter_code: Optional[str] = None
    solution_code: Optional[str] = None
    language: Optional[str] = None
    time_limit_seconds: int
    memory_limit_mb: int
    hints: Optional[List[str]] = None
    image_id: Optional[UUID] = None
    image: Optional[AttachmentResponse] = None
    test_cases: List[ProblemTestCaseResponse] = []
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Heading
# ---------------------------------------------------------------------------
class HeadingLessonCreate(LessonContentSchema):
    lesson_id: UUID
    text: str
    level: int = 1


class HeadingLessonUpdate(LessonContentSchema):
    text: Optional[str] = None
    level: Optional[int] = None


class HeadingLessonResponse(LessonContentSchema):
    id: UUID
    lesson_id: UUID
    text: str
    level: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Image
# ---------------------------------------------------------------------------
class ImageLessonCreate(LessonContentSchema):
    lesson_id: UUID
    image_id: UUID
    caption: Optional[str] = None
    alt_text: Optional[str] = None


class ImageLessonUpdate(LessonContentSchema):
    image_id: Optional[UUID] = None
    caption: Optional[str] = None
    alt_text: Optional[str] = None


class ImageLessonResponse(LessonContentSchema):
    id: UUID
    lesson_id: UUID
    image_id: UUID
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    image: Optional[AttachmentResponse] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Code
# ---------------------------------------------------------------------------
class CodeLessonCreate(LessonContentSchema):
    lesson_id: UUID
    code: str
    language: Optional[str] = None
    filename: Optional[str] = None
    show_line_numbers: bool = True


class CodeLessonUpdate(LessonContentSchema):
    code: Optional[str] = None
    language: Optional[str] = None
    filename: Optional[str] = None
    show_line_numbers: Optional[bool] = None


class CodeLessonResponse(LessonContentSchema):
    id: UUID
    lesson_id: UUID
    code: str
    language: Optional[str] = None
    filename: Optional[str] = None
    show_line_numbers: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Hint
# ---------------------------------------------------------------------------
class HintLessonCreate(LessonContentSchema):
    lesson_id: UUID
    text: str
    is_collapsible: bool = True


class HintLessonUpdate(LessonContentSchema):
    text: Optional[str] = None
    is_collapsible: Optional[bool] = None


class HintLessonResponse(LessonContentSchema):
    id: UUID
    lesson_id: UUID
    text: str
    is_collapsible: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Callout
# ---------------------------------------------------------------------------
class CalloutLessonCreate(LessonContentSchema):
    lesson_id: UUID
    text: str
    callout_type: str = "info"
    title: Optional[str] = None


class CalloutLessonUpdate(LessonContentSchema):
    text: Optional[str] = None
    callout_type: Optional[str] = None
    title: Optional[str] = None


class CalloutLessonResponse(LessonContentSchema):
    id: UUID
    lesson_id: UUID
    text: str
    callout_type: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
