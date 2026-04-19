from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime
from app.core.schema import BaseSchema
from app.attachment.schemas import AttachmentResponse
from app.lessons.schemas.lesson_contents import (
    CalloutLessonResponse,
    CalloutLessonUpsert,
    CodeLessonResponse,
    CodeLessonUpsert,
    HeadingLessonResponse,
    HeadingLessonUpsert,
    HintLessonResponse,
    HintLessonUpsert,
    ImageLessonResponse,
    ImageLessonUpsert,
    InteractiveLessonResponse,
    InteractiveLessonUpsert,
    ProblemLessonResponse,
    ProblemLessonUpsert,
    QuizLessonResponse,
    QuizLessonUpsert,
    TextLessonResponse,
    TextLessonUpsert,
    VideoLessonResponse,
    VideoLessonUpsert,
)
from app.lessons.models.lessons import LessonKind, LessonSettings


class SectionCreate(BaseSchema):
    title: str
    course_id: UUID
    order: int = 0
    url: Optional[str] = None
    duration: int = 0
    attachment_ids: Optional[List[UUID]] = None


class SectionUpdate(BaseSchema):
    title: Optional[str] = None
    order: Optional[int] = None
    url: Optional[str] = None
    duration: Optional[int] = None
    attachment_ids: Optional[List[UUID]] = None


class LessonCreate(BaseSchema):
    section_id: UUID
    tag: Optional[str] = None
    title: str
    kind: LessonKind = LessonKind.TEXT
    content: Optional[Any] = None
    position: int = 0
    duration_minutes: int = 0
    is_free: bool = False
    duration_minutes: int = 0
    xp_reward: int = 0
    difficulty: Optional[LessonSettings.DifficultyEnum] = None
    video_content: Optional[List[VideoLessonUpsert]] = None
    text_content: Optional[List[TextLessonUpsert]] = None
    quiz_content: Optional[List[QuizLessonUpsert]] = None
    interactive_content: Optional[List[InteractiveLessonUpsert]] = None
    problem_content: Optional[List[ProblemLessonUpsert]] = None
    heading_content: Optional[List[HeadingLessonUpsert]] = None
    image_content: Optional[List[ImageLessonUpsert]] = None
    code_content: Optional[List[CodeLessonUpsert]] = None
    hint_content: Optional[List[HintLessonUpsert]] = None
    callout_content: Optional[List[CalloutLessonUpsert]] = None


class LessonUpdate(BaseSchema):
    title: Optional[str] = None
    kind: Optional[LessonKind] = None
    content: Optional[Any] = None
    position: Optional[int] = None
    duration_minutes: Optional[int] = None
    is_free: Optional[bool] = None
    tag: Optional[str] = None
    duration_minutes: int = 0
    xp_reward: int = 0
    difficulty: Optional[LessonSettings.DifficultyEnum] = None
    video_content: Optional[List[VideoLessonUpsert]] = None
    text_content: Optional[List[TextLessonUpsert]] = None
    quiz_content: Optional[List[QuizLessonUpsert]] = None
    interactive_content: Optional[List[InteractiveLessonUpsert]] = None
    problem_content: Optional[List[ProblemLessonUpsert]] = None
    heading_content: Optional[List[HeadingLessonUpsert]] = None
    image_content: Optional[List[ImageLessonUpsert]] = None
    code_content: Optional[List[CodeLessonUpsert]] = None
    hint_content: Optional[List[HintLessonUpsert]] = None
    callout_content: Optional[List[CalloutLessonUpsert]] = None


class LessonResponse(BaseSchema):
    id: UUID
    tag: Optional[str] = None
    section_id: UUID
    title: str
    kind: LessonKind
    content: Optional[Any] = None
    position: int
    duration_minutes: int
    is_free: bool
    like_count: int
    share_count: int
    video_content: List[VideoLessonResponse] = []
    text_content: List[TextLessonResponse] = []
    quiz_content: List[QuizLessonResponse] = []
    interactive_content: List[InteractiveLessonResponse] = []
    problem_content: List[ProblemLessonResponse] = []
    heading_content: List[HeadingLessonResponse] = []
    image_content: List[ImageLessonResponse] = []
    code_content: List[CodeLessonResponse] = []
    hint_content: List[HintLessonResponse] = []
    callout_content: List[CalloutLessonResponse] = []
    created_at: datetime
    updated_at: datetime
    duration_minutes: int = 0
    xp_reward: int = 0
    difficulty: Optional[LessonSettings.DifficultyEnum] = None


class SectionResponse(BaseSchema):
    id: UUID
    title: str
    course_id: UUID
    order: int
    url: Optional[str] = None
    duration: int
    created_at: datetime
    updated_at: datetime
    lessons: List[LessonResponse] = []
    attachments: List[AttachmentResponse] = []


class CommentCreate(BaseSchema):
    lesson_id: UUID
    content: str
    parent_id: Optional[UUID] = None


class CommentResponse(BaseSchema):
    id: UUID
    lesson_id: UUID
    user_id: UUID
    content: str
    parent_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class BookmarkResponse(BaseSchema):
    id: UUID
    user_id: UUID
    lesson_id: UUID
    created_at: datetime
