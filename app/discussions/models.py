from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.core.models import BaseModel


class DiscussionPost(BaseModel):
    __tablename__ = "discussion_posts"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)

    user = relationship("User")
    replies = relationship(
        "DiscussionReply", back_populates="post", cascade="all, delete-orphan"
    )
    likes = relationship(
        "DiscussionLike", back_populates="post", cascade="all, delete-orphan"
    )


class DiscussionReply(BaseModel):
    __tablename__ = "discussion_replies"

    post_id = Column(PG_UUID(as_uuid=True), ForeignKey("discussion_posts.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(PG_UUID(as_uuid=True), ForeignKey("discussion_replies.id"), nullable=True)

    post = relationship("DiscussionPost", back_populates="replies")
    user = relationship("User")
    replies = relationship(
        "DiscussionReply", back_populates="parent", cascade="all, delete-orphan"
    )
    parent = relationship(
        "DiscussionReply", back_populates="replies", remote_side="DiscussionReply.id"
    )


class DiscussionLike(BaseModel):
    __tablename__ = "discussion_likes"

    post_id = Column(PG_UUID(as_uuid=True), ForeignKey("discussion_posts.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    post = relationship("DiscussionPost", back_populates="likes")
    user = relationship("User")
