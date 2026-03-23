from typing import Any, Optional
from uuid import UUID
from datetime import datetime
from app.core.schema import BaseSchema


class ProgressSave(BaseSchema):
    lesson_id: UUID
    percent: float
    state: Optional[Any] = None
    time_spent_seconds: int = 0


class ProgressResponse(BaseSchema):
    id: UUID
    user_id: UUID
    lesson_id: UUID
    percent: float
    completed: bool
    state: Optional[Any] = None
    time_spent_seconds: int
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

