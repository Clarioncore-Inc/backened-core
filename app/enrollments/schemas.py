from typing import Optional
from uuid import UUID
from datetime import datetime
from app.core.schema import BaseSchema


class EnrollmentCreate(BaseSchema):
    course_id: UUID


class EnrollmentResponse(BaseSchema):
    id: UUID
    user_id: UUID
    course_id: UUID
    status: str
    progress: float
    enrolled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

