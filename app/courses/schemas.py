from typing import Any, List, Literal, Optional
from uuid import UUID
from datetime import datetime
from app.core.schema import BaseSchema
from app.lessons.schemas import LessonCreate, LessonResponse, SectionResponse


class CourseCreate(BaseSchema):
    title: str
    description: str
    category: str
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    org_id: Optional[UUID] = None
    is_public: bool = True
    cover_image: Optional[str] = None
    sub_title: Optional[str] = None
    subcategory: Optional[str] = None
    price: float = 0
    discount: Optional[float] = None
    currency: str = "USD"
    estimated_hours: float = 0
    tags: Optional[List[str]] = None
    status: Literal["draft", "published", "archived"] = "draft"

    course_goals: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    who_this_course_is_for: Optional[str] = None
    enable_discussions: bool = True
    enable_reviews: bool = True
    enable_certificates: bool = False
    maximum_students: Optional[int] = None


class CourseUpdate(BaseSchema):
    title: Optional[str] = None
    sub_title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    is_public: Optional[bool] = None
    cover_image: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[float] = None
    discount: Optional[float] = None
    currency: Optional[str] = None
    estimated_hours: Optional[float] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    course_goals: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    who_this_course_is_for: Optional[str] = None
    enable_discussions: Optional[bool] = None
    enable_reviews: Optional[bool] = None
    enable_certificates: Optional[bool] = None
    maximum_students: Optional[int] = None


class CourseResponse(BaseSchema):
    id: UUID
    title: str
    sub_title: Optional[str] = None
    description: str
    category: str
    subcategory: Optional[str] = None
    level: str
    price: float
    discount: Optional[float] = None
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
    course_goals: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    who_this_course_is_for: Optional[str] = None
    enable_discussions: bool
    enable_reviews: bool
    enable_certificates: bool
    maximum_students: Optional[int] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CourseWithSections(CourseResponse):
    sections: List[SectionResponse] = []


class BulkLessonCreate(LessonCreate):
    section_id: Optional[UUID] = None


class BulkSectionCreate(BaseSchema):

    title: str
    order: int = 0
    url: Optional[str] = None
    duration: int = 0
    lessons: List[BulkLessonCreate] = []


class CourseBulkCreate(CourseCreate):
    sections: List[BulkSectionCreate] = []
