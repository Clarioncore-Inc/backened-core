from sqlalchemy import Column, Integer, String, Text
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
    threads = relationship(
        "ReviewThread", back_populates="review", cascade="all, delete-orphan"
    )


class ReviewThread(BaseModel):
    __tablename__ = "review_threads"

    review_id = Column(PG_UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(PG_UUID(as_uuid=True), ForeignKey("review_threads.id"), nullable=True)
    like_count = Column(Integer, default=0)
    dislike_count = Column(Integer, default=0)

    review = relationship("Review", back_populates="threads")
    user = relationship("User")
    replies = relationship(
        "ReviewThread", back_populates="parent", cascade="all, delete-orphan"
    )
    parent = relationship(
        "ReviewThread", back_populates="replies", remote_side="ReviewThread.id"
    )
    reactions = relationship(
        "ReviewThreadReaction", back_populates="thread", cascade="all, delete-orphan"
    )


class ReviewThreadReaction(BaseModel):
    __tablename__ = "review_thread_reactions"

    thread_id = Column(PG_UUID(as_uuid=True), ForeignKey("review_threads.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reaction = Column(String, nullable=False)

    thread = relationship("ReviewThread", back_populates="reactions")
    user = relationship("User")

