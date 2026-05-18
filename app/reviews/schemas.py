from enum import Enum
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.core.schema import BaseSchema
from app.accounts.schemas import UserResponse


class ReviewCreate(BaseSchema):
    course_id: UUID
    rating: int
    comment: Optional[str] = None


class ReviewUpdate(BaseSchema):
    rating: int
    comment: Optional[str] = None


class ReviewThreadCreate(BaseSchema):
    content: str
    parent_id: Optional[UUID] = None


class ReviewThreadReactionEnum(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"


class ReviewThreadReactionPayload(BaseSchema):
    reaction: ReviewThreadReactionEnum


class ReviewThreadResponse(BaseSchema):
    id: UUID
    review_id: UUID
    user_id: UUID
    user: Optional[UserResponse] = None
    content: str
    parent_id: Optional[UUID] = None
    like_count: int
    dislike_count: int
    created_at: datetime
    updated_at: datetime
    replies: List["ReviewThreadResponse"] = []


class ReviewResponse(BaseSchema):
    id: UUID
    course_id: UUID
    user_id: UUID
    user: Optional[UserResponse] = None
    rating: int
    comment: Optional[str] = None
    helpful_count: int
    created_at: datetime
    updated_at: datetime
    threads: List[ReviewThreadResponse] = []


ReviewThreadResponse.model_rebuild()
