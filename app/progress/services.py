from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.progress.models import LessonProgress
from app.accounts.models import User
from app.enrollments.services import EnrollmentService
from app.lessons.models import Lesson, Section

XP_PER_COMPLETION = 10
enrollment_service = EnrollmentService()


class ProgressService:
    def save_progress(self, db: Session, user_id, data: dict) -> LessonProgress:
        lesson_id = data["lesson_id"]
        lesson = (
            db.query(Lesson)
            .join(Section, Lesson.section_id == Section.id)
            .filter(Lesson.id == lesson_id)
            .first()
        )
        record = (
            db.query(LessonProgress)
            .filter(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id == lesson_id,
            )
            .first()
        )
        if record:
            for field, value in data.items():
                if field != "lesson_id":
                    setattr(record, field, value)
            record.last_seen_at = datetime.now(timezone.utc)
        else:
            record = LessonProgress(
                user_id=user_id,
                last_seen_at=datetime.now(timezone.utc),
                **data,
            )
            db.add(record)

        was_completed = record.completed
        if data.get("percent", 0) >= 100 and not was_completed:
            record.completed = True
            # Award XP
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.xp = (user.xp or 0) + XP_PER_COMPLETION
        elif data.get("percent", 0) < 100:
            record.completed = False

        db.flush()

        if lesson:
            enrollment_service.sync_progress(
                db=db,
                user_id=user_id,
                course_id=lesson.section.course_id,
                last_accessed=record.last_seen_at,
            )

        db.commit()
        db.refresh(record)
        return record

    def get_progress(self, db: Session, user_id, lesson_id) -> Optional[LessonProgress]:
        return (
            db.query(LessonProgress)
            .filter(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id == lesson_id,
            )
            .first()
        )

