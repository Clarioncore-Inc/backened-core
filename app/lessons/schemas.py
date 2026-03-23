from typing import Any, Optional
from uuid import UUID
from datetime import datetime
from app.core.schema import BaseSchema


class LessonCreate(BaseSchema):
    course_id: UUID
    title: str
    kind: str = "article"
    content: Optional[Any] = None
    position: int = 0
    duration_minutes: int = 0
    is_free: bool = False
    module_id: Optional[UUID] = None


class LessonResponse(BaseSchema):
    id: UUID
    course_id: UUID
    module_id: Optional[UUID] = None
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

