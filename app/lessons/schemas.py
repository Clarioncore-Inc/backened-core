from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime
from app.core.schema import BaseSchema


class SectionCreate(BaseSchema):
    title: str
    course_id: UUID
    order: int = 0
    url: Optional[str] = None
    duration: int = 0


class SectionUpdate(BaseSchema):
    title: Optional[str] = None
    order: Optional[int] = None
    url: Optional[str] = None
    duration: Optional[int] = None


class LessonCreate(BaseSchema):
    section_id: UUID
    title: str
    kind: str = "article"
    content: Optional[Any] = None
    position: int = 0
    duration_minutes: int = 0
    is_free: bool = False


class LessonUpdate(BaseSchema):
    title: Optional[str] = None
    kind: Optional[str] = None
    content: Optional[Any] = None
    position: Optional[int] = None
    duration_minutes: Optional[int] = None
    is_free: Optional[bool] = None


class LessonResponse(BaseSchema):
    id: UUID
    section_id: UUID
    title: str
    kind: str
    content: Optional[Any] = None
    position: int
    duration_minutes: int
    is_free: bool
    like_count: int
    share_count: int
    created_at: datetime
    updated_at: datetime


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
