from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.enrollments.models import Enrollment
from app.courses.models import Course
from app.lessons.models import Lesson, Section
from app.progress.models import LessonProgress


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

    def sync_progress(
        self,
        db: Session,
        user_id,
        course_id,
        last_accessed: Optional[datetime] = None,
    ) -> Optional[Enrollment]:
        enrollment = (
            db.query(Enrollment)
            .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
            .first()
        )
        if not enrollment:
            return None

        lesson_ids = [
            lesson_id
            for (lesson_id,) in db.query(Lesson.id)
            .join(Section, Lesson.section_id == Section.id)
            .filter(Section.course_id == course_id)
            .all()
        ]

        now = last_accessed or datetime.now(timezone.utc)
        enrollment.last_accessed = now

        if not lesson_ids:
            db.flush()
            return enrollment

        progress_records = (
            db.query(LessonProgress)
            .filter(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id.in_(lesson_ids),
            )
            .all()
        )

        progress_by_lesson = {
            record.lesson_id: min(float(record.percent or 0), 100)
            for record in progress_records
        }
        total_percent = sum(progress_by_lesson.get(lesson_id, 0) for lesson_id in lesson_ids)
        computed_progress = round(total_percent / len(lesson_ids)) if lesson_ids else 0
        all_completed = all(progress_by_lesson.get(lesson_id, 0) >= 100 for lesson_id in lesson_ids)

        enrollment.progress = min(max(computed_progress, 0), 100)

        if enrollment.status != "dropped":
            if all_completed:
                enrollment.status = "completed"
                enrollment.progress = 100
                enrollment.completed_at = enrollment.completed_at or now
            else:
                enrollment.status = "active"
                enrollment.completed_at = None

        db.flush()
        return enrollment

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

