from sqlalchemy import Boolean, Column, DateTime, Float, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.models import BaseModel


class LessonProgress(BaseModel):
    __tablename__ = "lesson_progress"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lesson_id = Column(PG_UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)
    percent = Column(Float, default=0)
    completed = Column(Boolean, default=False)
    state = Column(JSONB, nullable=True)
    time_spent_seconds = Column(Integer, default=0)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="progress_records")
    lesson = relationship("Lesson", back_populates="progress_records")

