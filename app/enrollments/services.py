from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.enrollments.models import Enrollment
from app.courses.models import Course


class EnrollmentService:
    def enroll(self, db: Session, user_id, course_id) -> Enrollment:
        existing = (
            db.query(Enrollment)
            .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
            .first()
        )
        if existing:
            return existing
        enrollment = Enrollment(
            user_id=user_id,
            course_id=course_id,
            enrolled_at=datetime.now(timezone.utc),
        )
        db.add(enrollment)
        # Bump enrollment count
        course = db.query(Course).filter(Course.id == course_id).first()
        if course:
            course.total_enrollments = (course.total_enrollments or 0) + 1
        db.commit()
        db.refresh(enrollment)
        return enrollment

    def get_user_enrollments(self, db: Session, user_id) -> List[Enrollment]:
        return db.query(Enrollment).filter(Enrollment.user_id == user_id).all()

    def get_course_enrollments(self, db: Session, course_id) -> List[Enrollment]:
        return db.query(Enrollment).filter(Enrollment.course_id == course_id).all()

    def unenroll(self, db: Session, enrollment_id, user_id) -> bool:
        enrollment = (
            db.query(Enrollment)
            .filter(Enrollment.id == enrollment_id, Enrollment.user_id == user_id)
            .first()
        )
        if not enrollment:
            return False
        db.delete(enrollment)
        db.commit()
        return True

