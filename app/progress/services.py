from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.progress.models import LessonProgress
from app.accounts.models import User

XP_PER_COMPLETION = 10


class ProgressService:
    def save_progress(self, db: Session, user_id, data: dict) -> LessonProgress:
        lesson_id = data["lesson_id"]
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

