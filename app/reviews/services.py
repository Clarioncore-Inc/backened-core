from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.reviews.models import Review
from app.courses.models import Course


class ReviewService:
    def create_review(self, db: Session, user_id, data: dict) -> Review:
        data["user_id"] = user_id
        review = Review(**data)
        db.add(review)
        db.flush()

        # Recalculate course rating
        course_id = data["course_id"]
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

        db.commit()
        db.refresh(review)
        return review

    def get_course_reviews(self, db: Session, course_id) -> List[Review]:
        return db.query(Review).filter(Review.course_id == course_id).all()

