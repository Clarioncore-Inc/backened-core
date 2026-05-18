from typing import List

from sqlalchemy.orm import Session

from app.discussions.models import DiscussionLike, DiscussionPost, DiscussionReply
from app.discussions.schemas import DiscussionPostResponse, DiscussionReplyResponse


class DiscussionService:
    def _serialize_reply(self, reply: DiscussionReply) -> DiscussionReplyResponse:
        child_replies = sorted(reply.replies or [], key=lambda item: item.created_at)
        return DiscussionReplyResponse(
            id=reply.id,
            post_id=reply.post_id,
            user_id=reply.user_id,
            user=reply.user,
            content=reply.content,
            parent_id=reply.parent_id,
            created_at=reply.created_at,
            updated_at=reply.updated_at,
            replies=[self._serialize_reply(child) for child in child_replies],
        )

    def _serialize_post(self, post: DiscussionPost) -> DiscussionPostResponse:
        top_level_replies = sorted(
            [reply for reply in (post.replies or []) if reply.parent_id is None],
            key=lambda item: item.created_at,
        )
        return DiscussionPostResponse(
            id=post.id,
            user_id=post.user_id,
            user=post.user,
            title=post.title,
            category=post.category,
            content=post.content,
            like_count=post.like_count,
            created_at=post.created_at,
            updated_at=post.updated_at,
            replies=[self._serialize_reply(reply) for reply in top_level_replies],
        )

    def list_posts(self, db: Session, category: str | None = None) -> List[DiscussionPostResponse]:
        query = db.query(DiscussionPost)
        if category:
            query = query.filter(DiscussionPost.category == category)
        posts = query.order_by(DiscussionPost.created_at.desc()).all()
        return [self._serialize_post(post) for post in posts]

    def get_post(self, db: Session, post_id) -> DiscussionPostResponse | None:
        post = db.query(DiscussionPost).filter(DiscussionPost.id == post_id).first()
        if not post:
            return None
        return self._serialize_post(post)

    def create_post(self, db: Session, user_id, data: dict) -> DiscussionPostResponse:
        post = DiscussionPost(user_id=user_id, **data)
        db.add(post)
        db.commit()
        db.refresh(post)
        return self._serialize_post(post)

    def _get_post_model(self, db: Session, post_id) -> DiscussionPost | None:
        return db.query(DiscussionPost).filter(DiscussionPost.id == post_id).first()

    def create_reply(self, db: Session, post_id, user_id, data: dict) -> DiscussionReply | None:
        post = self._get_post_model(db, post_id)
        if not post:
            return None

        parent_id = data.get("parent_id")
        if parent_id:
            parent = db.query(DiscussionReply).filter(DiscussionReply.id == parent_id).first()
            if not parent or str(parent.post_id) != str(post_id):
                raise ValueError("Parent reply does not belong to this discussion")

        reply = DiscussionReply(post_id=post_id, user_id=user_id, **data)
        db.add(reply)
        db.commit()
        db.refresh(reply)
        return reply

    def toggle_like(self, db: Session, post_id, user_id) -> DiscussionPostResponse | None:
        post = self._get_post_model(db, post_id)
        if not post:
            return None

        existing = (
            db.query(DiscussionLike)
            .filter(DiscussionLike.post_id == post_id, DiscussionLike.user_id == user_id)
            .first()
        )

        if existing:
            db.delete(existing)
            post.like_count = max((post.like_count or 0) - 1, 0)
        else:
            db.add(DiscussionLike(post_id=post_id, user_id=user_id))
            post.like_count = (post.like_count or 0) + 1

        db.commit()
        db.refresh(post)
        return self._serialize_post(post)
