from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.core.models import BaseModel


class Note(BaseModel):
    __tablename__ = "notes"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(PG_UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True)
    lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False, default="")
    tags = Column(ARRAY(String), nullable=True, default=list)
    color = Column(String, nullable=False, default="blue")
    is_pinned = Column(Boolean, nullable=False, default=False)

    course = relationship("Course")
    lesson = relationship("Lesson")

    @property
    def course_title(self):
        return self.course.title if self.course else None

    @property
    def lesson_title(self):
        return self.lesson.title if self.lesson else None
