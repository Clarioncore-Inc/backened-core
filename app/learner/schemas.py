from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import Field

from app.core.schema import BaseResponseSchema, BaseSchema


class LearningGoalTypeEnum(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class LearningGoalUnitEnum(str, Enum):
    LESSONS = "lessons"
    HOURS = "hours"
    COURSES = "courses"
    QUIZZES = "quizzes"


class LearningGoalCreate(BaseSchema):
    title: str
    description: Optional[str] = None
    type: LearningGoalTypeEnum
    target: float
    unit: LearningGoalUnitEnum
    deadline: Optional[datetime] = None


class LearningGoalUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[LearningGoalTypeEnum] = None
    target: Optional[float] = None
    current: Optional[float] = None
    unit: Optional[LearningGoalUnitEnum] = None
    deadline: Optional[datetime] = None
    completed: Optional[bool] = None


class LearningGoalResponse(BaseResponseSchema):
    user_id: UUID
    title: str
    description: Optional[str] = None
    type: LearningGoalTypeEnum = Field(alias="goal_type")
    target: float
    current: float
    unit: LearningGoalUnitEnum
    deadline: Optional[datetime] = None
    completed: bool


class StudyStatsTodayResponse(BaseSchema):
    lessons: int
    hours: float
    quizzes: int


class StudyStatsPeriodResponse(StudyStatsTodayResponse):
    courses: int = 0


class StudyStatsResponse(BaseSchema):
    today: StudyStatsTodayResponse
    this_week: StudyStatsPeriodResponse
    this_month: StudyStatsPeriodResponse
    streak: int
    total_study_time: float


class LearningStreakResponse(BaseSchema):
    current: int
    longest: int
    last_active: Optional[date] = None
    total_days: int
    freezes_available: int
    calendar: Dict[str, int]


class LearningActivityLog(BaseSchema):
    minutes: int = 15
    lessons_completed: int = 0
    quizzes_completed: int = 0
    courses_completed: int = 0
    activity_date: Optional[date] = None


class UseStreakFreezePayload(BaseSchema):
    activity_date: Optional[date] = None


class ProgressDashboardStatsResponse(BaseSchema):
    total_courses: int
    completed_courses: int
    in_progress_courses: int
    total_hours_learned: float
    average_progress: float
    current_streak: int
    longest_streak: int
    total_points: int
    certificates_earned: int
    lessons_completed: int


class ProgressDashboardEnrollmentResponse(BaseSchema):
    id: UUID
    course_id: UUID
    course_title: str
    progress: float
    completed: bool
    enrolled_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None


class WeeklyActivityItemResponse(BaseSchema):
    day: str
    date: date
    minutes: int


class RecentActivityItemResponse(BaseSchema):
    type: str
    text: str
    occurred_at: datetime


class ProgressDashboardResponse(BaseSchema):
    stats: ProgressDashboardStatsResponse
    enrollments: List[ProgressDashboardEnrollmentResponse]
    weekly_activity: List[WeeklyActivityItemResponse]
    recent_activity: List[RecentActivityItemResponse]
