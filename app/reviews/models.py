from sqlalchemy import Column, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.models import BaseModel


class Review(BaseModel):
    __tablename__ = "reviews"

    course_id = Column(PG_UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    helpful_count = Column(Integer, default=0)

    # Relationships
    course = relationship("Course", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

