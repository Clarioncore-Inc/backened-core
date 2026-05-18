from enum import Enum
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.schema import BaseSchema
from app.accounts.schemas import UserResponse


class DiscussionCategoryEnum(str, Enum):
    GENERAL_DISCUSSION = "general_discussion"
    QUESTION = "question"
    RESOURCE = "resource"


class DiscussionCreate(BaseSchema):
    title: str
    category: DiscussionCategoryEnum
    content: str


class DiscussionReplyCreate(BaseSchema):
    content: str
    parent_id: Optional[UUID] = None


class DiscussionReplyResponse(BaseSchema):
    id: UUID
    post_id: UUID
    user_id: UUID
    user: Optional[UserResponse] = None
    content: str
    parent_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    replies: List["DiscussionReplyResponse"] = []


class DiscussionPostResponse(BaseSchema):
    id: UUID
    user_id: UUID
    user: Optional[UserResponse] = None
    title: str
    category: DiscussionCategoryEnum
    content: str
    like_count: int
    created_at: datetime
    updated_at: datetime
    replies: List[DiscussionReplyResponse] = []


DiscussionReplyResponse.model_rebuild()
