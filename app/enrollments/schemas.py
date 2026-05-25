from typing import Optional
from uuid import UUID
from datetime import datetime
from app.core.schema import BaseSchema
from app.courses.schemas import CourseResponse


class EnrollmentCreate(BaseSchema):
    course_id: UUID


class EnrollmentResponse(BaseSchema):
    id: UUID
    user_id: UUID
    course: CourseResponse
    status: str
    completed: bool = False
    progress: float
    enrolled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

