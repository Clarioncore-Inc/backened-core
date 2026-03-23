from typing import Optional
from uuid import UUID
from datetime import datetime
from app.core.schema import BaseSchema


class ReviewCreate(BaseSchema):
    course_id: UUID
    rating: int
    comment: Optional[str] = None


class ReviewResponse(BaseSchema):
    id: UUID
    course_id: UUID
    user_id: UUID
    rating: int
    comment: Optional[str] = None
    helpful_count: int
    created_at: datetime
    updated_at: datetime

