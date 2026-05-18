from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.models import BaseModel


class LearningGoal(BaseModel):
    __tablename__ = "learning_goals"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    goal_type = Column(String, nullable=False)
    target = Column(Float, nullable=False)
    current = Column(Float, default=0)
    unit = Column(String, nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=True)
    completed = Column(Boolean, default=False)


class LearnerProfile(BaseModel):
    __tablename__ = "learner_profiles"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    longest_streak = Column(Integer, default=0)
    freezes_available = Column(Integer, default=2)


class LearnerDailyActivity(BaseModel):
    __tablename__ = "learner_daily_activity"
    __table_args__ = (
        UniqueConstraint("user_id", "activity_date", name="uq_learner_daily_activity_user_date"),
    )

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    activity_date = Column(Date, nullable=False)
    minutes = Column(Integer, default=0)
    lessons_completed = Column(Integer, default=0)
    quizzes_completed = Column(Integer, default=0)
    courses_completed = Column(Integer, default=0)
    freeze_used = Column(Boolean, default=False)
