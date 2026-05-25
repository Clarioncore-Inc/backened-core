from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.core.schema import BaseSchema, BaseResponseSchema


class NoteCreate(BaseSchema):
    title: str
    content: str = ""
    course_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)
    color: str = "blue"


class NoteUpdate(BaseSchema):
    title: Optional[str] = None
    content: Optional[str] = None
    course_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    color: Optional[str] = None
    is_pinned: Optional[bool] = None


class NotePinUpdate(BaseSchema):
    is_pinned: bool


class NoteResponse(BaseResponseSchema):
    user_id: UUID
    title: str
    content: str
    course_id: Optional[UUID] = None
    course_title: Optional[str] = None
    lesson_id: Optional[UUID] = None
    lesson_title: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    color: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
