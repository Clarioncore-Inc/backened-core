from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import field_validator, field_serializer
from app.core.schema import BaseSchema
from app.attachment.schemas import AttachmentResponse
from app.lessons.models.lesson_contents import LessonContentMixin


class LessonContentSchemaMixin(BaseSchema):
    parent_id: Optional[UUID] = None
    parent_type: Optional[LessonContentMixin.ParentType] = None
    position: int = 0

    @field_validator('parent_id', mode='before')
    @classmethod
    def empty_string_to_none_uuid(cls, v):
        """Convert empty strings to None for optional UUID fields"""
        if v == "" or v == "null":
            return None
        return v

    @field_validator('parent_type', mode='before')
    @classmethod
    def empty_string_to_none_enum(cls, v):
        """Convert empty strings to None for optional enum fields"""
        if v == "" or v == "null":
            return None
        return v


class ChildContentResponse(BaseSchema):
    video_content: List['VideoLessonResponse'] = []
    text_content: List['TextLessonResponse'] = []
    quiz_content: List['QuizLessonResponse'] = []
    interactive_content: List['InteractiveLessonResponse'] = []
    problem_content: List['ProblemLessonResponse'] = []
    heading_content: List['HeadingLessonResponse'] = []
    image_content: List['ImageLessonResponse'] = []
    code_content: List['CodeLessonResponse'] = []
    hint_content: List['HintLessonResponse'] = []
    callout_content: List['CalloutLessonResponse'] = []

    def is_empty(self) -> bool:
        """Check if all content lists are empty"""
        return all([
            not self.video_content,
            not self.text_content,
            not self.quiz_content,
            not self.interactive_content,
            not self.problem_content,
            not self.heading_content,
            not self.image_content,
            not self.code_content,
            not self.hint_content,
            not self.callout_content,
        ])


class ContentWithChildrenMixin(LessonContentSchemaMixin):
    children: Optional[ChildContentResponse] = None

    @field_serializer('children')
    def serialize_children(self, value: Optional[ChildContentResponse]) -> Optional[ChildContentResponse]:
        """Return None for children if it has no content"""
        if value is None or value.is_empty():
            return None
        return value


# ---------------------------------------------------------------------------
# Video
# ---------------------------------------------------------------------------
class VideoLessonCreate(LessonContentSchemaMixin):
    lesson_id: UUID
    video_id: Optional[UUID] = None
    external_url: Optional[str] = None
    duration_seconds: int = 0
    thumbnail_id: Optional[UUID] = None
    transcript: Optional[str] = None
    subtitles_id: Optional[UUID] = None
    allow_download: bool = False


class VideoLessonUpdate(LessonContentSchemaMixin):
    video_id: Optional[UUID] = None
    external_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    thumbnail_id: Optional[UUID] = None
    transcript: Optional[str] = None
    subtitles_id: Optional[UUID] = None
    allow_download: Optional[bool] = None


class VideoLessonResponse(ContentWithChildrenMixin):
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
class TextLessonAttachmentResponse(LessonContentSchemaMixin):
    id: UUID
    attachment: AttachmentResponse


class TextLessonCreate(LessonContentSchemaMixin):
    lesson_id: UUID
    body: str
    estimated_read_minutes: int = 0
    attachment_ids: Optional[List[UUID]] = None


class TextLessonUpdate(LessonContentSchemaMixin):
    body: Optional[str] = None
    estimated_read_minutes: Optional[int] = None
    attachment_ids: Optional[List[UUID]] = None


class TextLessonResponse(ContentWithChildrenMixin):
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
class QuizQuestionOptionCreate(LessonContentSchemaMixin):
    text: str
    is_correct: bool = False
    position: int = 0


class QuizQuestionOptionUpdate(LessonContentSchemaMixin):
    text: Optional[str] = None
    is_correct: Optional[bool] = None
    position: Optional[int] = None


class QuizQuestionOptionResponse(LessonContentSchemaMixin):
    id: UUID
    text: str
    is_correct: bool
    position: int


class QuizQuestionCreate(LessonContentSchemaMixin):
    question_type: str = "single_choice"
    text: str
    explanation: Optional[str] = None
    image_id: Optional[UUID] = None
    position: int = 0
    points: int = 1
    options: List[QuizQuestionOptionCreate] = []


class QuizQuestionUpdate(LessonContentSchemaMixin):
    question_type: Optional[str] = None
    text: Optional[str] = None
    explanation: Optional[str] = None
    image_id: Optional[UUID] = None
    position: Optional[int] = None
    points: Optional[int] = None
    options: Optional[List[QuizQuestionOptionCreate]] = None


class QuizQuestionResponse(LessonContentSchemaMixin):
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


class QuizLessonCreate(LessonContentSchemaMixin):
    lesson_id: UUID
    passing_score: int = 70
    max_attempts: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    shuffle_questions: bool = False
    show_correct_answers: bool = True
    questions: List[QuizQuestionCreate] = []


class QuizLessonUpdate(LessonContentSchemaMixin):
    passing_score: Optional[int] = None
    max_attempts: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    shuffle_questions: Optional[bool] = None
    show_correct_answers: Optional[bool] = None
    questions: Optional[List[QuizQuestionCreate]] = None


class QuizLessonResponse(ContentWithChildrenMixin):
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
class InteractiveStepCreate(LessonContentSchemaMixin):
    step_type: str
    title: Optional[str] = None
    instructions: Optional[str] = None
    position: int = 0
    payload: Dict[str, Any] = {}
    image_id: Optional[UUID] = None
    points: int = 1


class InteractiveStepUpdate(LessonContentSchemaMixin):
    step_type: Optional[str] = None
    title: Optional[str] = None
    instructions: Optional[str] = None
    position: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None
    image_id: Optional[UUID] = None
    points: Optional[int] = None


class InteractiveStepResponse(LessonContentSchemaMixin):
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


class InteractiveLessonCreate(LessonContentSchemaMixin):
    lesson_id: UUID
    passing_score: int = 70
    steps: List[InteractiveStepCreate] = []


class InteractiveLessonUpdate(LessonContentSchemaMixin):
    passing_score: Optional[int] = None
    steps: Optional[List[InteractiveStepCreate]] = None


class InteractiveLessonResponse(ContentWithChildrenMixin):
    id: UUID
    lesson_id: UUID
    passing_score: int
    steps: List[InteractiveStepResponse] = []
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Problem
# ---------------------------------------------------------------------------
class ProblemTestCaseCreate(LessonContentSchemaMixin):
    input: str
    expected_output: str
    is_sample: bool = False
    position: int = 0


class ProblemTestCaseUpdate(LessonContentSchemaMixin):
    input: Optional[str] = None
    expected_output: Optional[str] = None
    is_sample: Optional[bool] = None
    position: Optional[int] = None


class ProblemTestCaseResponse(LessonContentSchemaMixin):
    id: UUID
    input: str
    expected_output: str
    is_sample: bool
    position: int


class ProblemLessonCreate(LessonContentSchemaMixin):
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


class ProblemLessonUpdate(LessonContentSchemaMixin):
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


class ProblemLessonResponse(ContentWithChildrenMixin):
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
class HeadingLessonCreate(LessonContentSchemaMixin):
    lesson_id: UUID
    text: str
    level: int = 1


class HeadingLessonUpdate(LessonContentSchemaMixin):
    text: Optional[str] = None
    level: Optional[int] = None


class HeadingLessonResponse(ContentWithChildrenMixin):
    id: UUID
    lesson_id: UUID
    text: str
    level: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Image
# ---------------------------------------------------------------------------
class ImageLessonCreate(LessonContentSchemaMixin):
    lesson_id: UUID
    image_id: UUID
    caption: Optional[str] = None
    alt_text: Optional[str] = None


class ImageLessonUpdate(LessonContentSchemaMixin):
    image_id: Optional[UUID] = None
    caption: Optional[str] = None
    alt_text: Optional[str] = None


class ImageLessonResponse(ContentWithChildrenMixin):
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
class CodeLessonCreate(LessonContentSchemaMixin):
    lesson_id: UUID
    code: str
    language: Optional[str] = None
    filename: Optional[str] = None
    show_line_numbers: bool = True


class CodeLessonUpdate(LessonContentSchemaMixin):
    code: Optional[str] = None
    language: Optional[str] = None
    filename: Optional[str] = None
    show_line_numbers: Optional[bool] = None


class CodeLessonResponse(ContentWithChildrenMixin):
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
class HintLessonCreate(LessonContentSchemaMixin):
    lesson_id: UUID
    text: str
    is_collapsible: bool = True


class HintLessonUpdate(LessonContentSchemaMixin):
    text: Optional[str] = None
    is_collapsible: Optional[bool] = None


class HintLessonResponse(ContentWithChildrenMixin):
    id: UUID
    lesson_id: UUID
    text: str
    is_collapsible: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Callout
# ---------------------------------------------------------------------------
class CalloutLessonCreate(LessonContentSchemaMixin):
    lesson_id: UUID
    text: str
    callout_type: str = "info"
    title: Optional[str] = None


class CalloutLessonUpdate(LessonContentSchemaMixin):
    text: Optional[str] = None
    callout_type: Optional[str] = None
    title: Optional[str] = None


class CalloutLessonResponse(ContentWithChildrenMixin):
    id: UUID
    lesson_id: UUID
    text: str
    callout_type: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime


VideoLessonResponse.model_rebuild()
TextLessonResponse.model_rebuild()
QuizLessonResponse.model_rebuild()
InteractiveLessonResponse.model_rebuild()
ProblemLessonResponse.model_rebuild()
HeadingLessonResponse.model_rebuild()
ImageLessonResponse.model_rebuild()
CodeLessonResponse.model_rebuild()
HintLessonResponse.model_rebuild()
CalloutLessonResponse.model_rebuild()
ChildContentResponse.model_rebuild()
