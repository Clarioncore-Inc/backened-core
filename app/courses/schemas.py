from typing import Any, List, Literal, Optional
from uuid import UUID
from datetime import datetime
from app.core.schema import BaseSchema
from app.lessons.schemas import LessonCreate, LessonResponse, SectionResponse
from app.reviews.schemas import ReviewResponse
from pydantic import model_validator
from app.attachment.schemas import AttachmentResponse


class CourseCreate(BaseSchema):
    title: str
    description: str
    category: str
    level: Literal["beginner", "intermediate",
                   "advanced", "all_levels"] = "beginner"
    org_id: Optional[UUID] = None
    is_public: bool = True
    cover_image: Optional[UUID] = None
    thumbnail: Optional[UUID] = None
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
    cover_image: Optional[UUID] = None
    thumbnail: Optional[UUID] = None
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
    total_lessons: int = 0
    total_duration_minutes: int = 0
    total_duration_text: str = "0m"
    duration: str = "0m"
    estimated_hours: float
    tags: Optional[List[str]] = None
    cover_image: Optional[AttachmentResponse] = None
    thumbnail: Optional[AttachmentResponse] = None
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

    @model_validator(mode="before")
    @classmethod
    def resolve_attachments(cls, obj):
        if hasattr(obj, "cover_image_attachment"):
            obj.__dict__["cover_image"] = obj.cover_image_attachment
        if hasattr(obj, "thumbnail_attachment"):
            obj.__dict__["thumbnail"] = obj.thumbnail_attachment
        return obj


class CourseWithSections(CourseResponse):
    sections: List[SectionResponse] = []
    reviews: List[ReviewResponse] = []


class BulkLessonCreate(LessonCreate):
    section_id: Optional[UUID] = None


class BulkSectionCreate(BaseSchema):
    title: str
    order: int = 0
    url: Optional[str] = None
    duration: int = 0
    lessons: List[BulkLessonCreate] = []
    attachment_ids: Optional[List[UUID]] = None


class CourseBulkCreate(CourseCreate):
    sections: List[BulkSectionCreate] = []


class BulkLessonUpdate(BaseSchema):
    id: Optional[UUID] = None
    title: Optional[str] = None
    kind: Optional[str] = None
    content: Optional[Any] = None
    position: Optional[int] = None
    duration_minutes: Optional[int] = None
    is_free: Optional[bool] = None


class BulkSectionUpdate(BaseSchema):
    id: Optional[UUID] = None
    title: Optional[str] = None
    order: Optional[int] = None
    url: Optional[str] = None
    duration: Optional[int] = None
    lessons: Optional[List[BulkLessonUpdate]] = None
    attachment_ids: Optional[List[UUID]] = None


class CourseBulkUpdate(CourseUpdate):
    sections: Optional[List[BulkSectionUpdate]] = None
