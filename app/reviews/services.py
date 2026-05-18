from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.reviews.models import Review, ReviewThread, ReviewThreadReaction
from app.courses.models import Course


class ReviewService:
    def _refresh_course_rating(self, db: Session, course_id) -> None:
        avg = (
            db.query(func.avg(Review.rating))
            .filter(Review.course_id == course_id)
            .scalar()
        )
        count = (
            db.query(func.count(Review.id))
            .filter(Review.course_id == course_id)
            .scalar()
        )
        course = db.query(Course).filter(Course.id == course_id).first()
        if course:
            course.rating = float(avg or 0)
            course.total_reviews = count or 0

    def create_review(self, db: Session, user_id, data: dict) -> Review:
        data["user_id"] = user_id
        review = Review(**data)
        db.add(review)
        db.flush()

        # Recalculate course rating
        course_id = data["course_id"]
        self._refresh_course_rating(db, course_id)

        db.commit()
        db.refresh(review)
        return review

    def update_review(self, db: Session, review_id, user_id, data: dict) -> Review | None:
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            return None
        if str(review.user_id) != str(user_id):
            raise PermissionError("Only the review creator can edit this review")

        review.rating = data["rating"]
        review.comment = data.get("comment")
        self._refresh_course_rating(db, review.course_id)

        db.commit()
        db.refresh(review)
        return review

    def delete_review(self, db: Session, review_id, user_id, user_role: str) -> bool:
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            return False
        if str(review.user_id) != str(user_id) and user_role != "admin":
            raise PermissionError("Only the review creator or an admin can delete this review")

        course_id = review.course_id
        db.delete(review)
        self._refresh_course_rating(db, course_id)
        db.commit()
        return True

    def get_course_reviews(self, db: Session, course_id) -> List[Review]:
        return db.query(Review).filter(Review.course_id == course_id).all()

    def get_review_threads(self, db: Session, review_id) -> List[ReviewThread]:
        return (
            db.query(ReviewThread)
            .filter(ReviewThread.review_id == review_id, ReviewThread.parent_id.is_(None))
            .order_by(ReviewThread.created_at.asc())
            .all()
        )

    def create_review_thread(self, db: Session, review_id, user_id, data: dict) -> ReviewThread | None:
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            return None

        parent_id = data.get("parent_id")
        if parent_id:
            parent = db.query(ReviewThread).filter(ReviewThread.id == parent_id).first()
            if not parent or str(parent.review_id) != str(review_id):
                raise ValueError("Parent thread does not belong to this review")

        thread = ReviewThread(review_id=review_id, user_id=user_id, **data)
        db.add(thread)
        db.commit()
        db.refresh(thread)
        return thread

    def react_to_review_thread(self, db: Session, thread_id, user_id, reaction: str) -> ReviewThread | None:
        thread = db.query(ReviewThread).filter(ReviewThread.id == thread_id).first()
        if not thread:
            return None

        existing = (
            db.query(ReviewThreadReaction)
            .filter(
                ReviewThreadReaction.thread_id == thread_id,
                ReviewThreadReaction.user_id == user_id,
            )
            .first()
        )

        def decrement_count(kind: str):
            if kind == "like":
                thread.like_count = max((thread.like_count or 0) - 1, 0)
            elif kind == "dislike":
                thread.dislike_count = max((thread.dislike_count or 0) - 1, 0)

        def increment_count(kind: str):
            if kind == "like":
                thread.like_count = (thread.like_count or 0) + 1
            elif kind == "dislike":
                thread.dislike_count = (thread.dislike_count or 0) + 1

        if existing:
            if existing.reaction == reaction:
                decrement_count(existing.reaction)
                db.delete(existing)
            else:
                decrement_count(existing.reaction)
                existing.reaction = reaction
                increment_count(reaction)
        else:
            db.add(ReviewThreadReaction(thread_id=thread_id, user_id=user_id, reaction=reaction))
            increment_count(reaction)

        db.commit()
        db.refresh(thread)
        return thread

