from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import Field
from app.core.schema import BaseSchema


class CourseCreate(BaseSchema):
    title: str
    description: str
    category: str
    level: str = "beginner"
    org_id: Optional[UUID] = None
    is_public: bool = True
    cover_image: Optional[str] = None
    subcategory: Optional[str] = None
    price: float = 0
    currency: str = "USD"
    estimated_hours: float = 0
    tags: Optional[List[str]] = None
    status: str = "draft"


class CourseUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    is_public: Optional[bool] = None
    cover_image: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    estimated_hours: Optional[float] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class CourseResponse(BaseSchema):
    id: UUID
    title: str
    description: str
    category: str
    subcategory: Optional[str] = None
    level: str
    price: Any  # Numeric can be Decimal
    currency: str
    is_public: bool
    status: str
    created_by: UUID
    org_id: Optional[UUID] = None
    rating: float
    total_reviews: int
    total_enrollments: int
    estimated_hours: float
    tags: Optional[List[str]] = None
    cover_image: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CourseWithLessons(CourseResponse):
    lessons: List[Any] = Field(default_factory=list)

