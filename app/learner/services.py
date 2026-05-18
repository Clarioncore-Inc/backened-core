from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.accounts.models import User
from app.courses.models import Course, CourseActivity
from app.enrollments.models import Enrollment
from app.learner.models import LearnerDailyActivity, LearnerProfile, LearningGoal
from app.learner.schemas import (
    LearningStreakResponse,
    ProgressDashboardEnrollmentResponse,
    ProgressDashboardResponse,
    ProgressDashboardStatsResponse,
    RecentActivityItemResponse,
    StudyStatsPeriodResponse,
    StudyStatsResponse,
    StudyStatsTodayResponse,
    WeeklyActivityItemResponse,
)
from app.lessons.models import Lesson, Section
from app.progress.models import LessonProgress

ACTIVE_STREAK_MINUTES = 15


class LearnerService:
    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _today(self) -> date:
        return self._now().date()

    def _hours_from_minutes(self, minutes: int) -> float:
        return round((minutes or 0) / 60, 1)

    def _get_or_create_profile(self, db: Session, user_id) -> LearnerProfile:
        profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
        if not profile:
            profile = LearnerProfile(user_id=user_id)
            db.add(profile)
            db.flush()
        return profile

    def _build_calendar_map(
        self,
        activities: List[LearnerDailyActivity],
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> Dict[str, int]:
        calendar: Dict[str, int] = {}
        for activity in activities:
            if year and activity.activity_date.year != year:
                continue
            if month and activity.activity_date.month != month:
                continue
            calendar[activity.activity_date.isoformat()] = int(activity.minutes or 0)
        return calendar

    def _compute_streak_metrics(self, activities: List[LearnerDailyActivity]) -> dict:
        qualifying_dates = sorted(
            activity.activity_date
            for activity in activities
            if (activity.minutes or 0) >= ACTIVE_STREAK_MINUTES
        )
        longest = 0
        running = 0
        previous_date: Optional[date] = None

        for activity_date in qualifying_dates:
            if previous_date and (activity_date - previous_date).days == 1:
                running += 1
            else:
                running = 1
            longest = max(longest, running)
            previous_date = activity_date

        current = 0
        today = self._today()
        if qualifying_dates:
            last_date = qualifying_dates[-1]
            if 0 <= (today - last_date).days <= 1:
                current = 1
                previous_date = last_date
                for activity_date in reversed(qualifying_dates[:-1]):
                    if (previous_date - activity_date).days == 1:
                        current += 1
                        previous_date = activity_date
                    else:
                        break

        active_dates = [activity.activity_date for activity in activities if (activity.minutes or 0) > 0]
        return {
            "current": current,
            "longest": longest,
            "last_active": max(active_dates) if active_dates else None,
            "total_days": len(active_dates),
        }

    def _refresh_streak_state(self, db: Session, user_id) -> tuple[User, LearnerProfile, List[LearnerDailyActivity], dict]:
        user = db.query(User).filter(User.id == user_id).first()
        profile = self._get_or_create_profile(db=db, user_id=user_id)
        activities = (
            db.query(LearnerDailyActivity)
            .filter(LearnerDailyActivity.user_id == user_id)
            .order_by(LearnerDailyActivity.activity_date.asc())
            .all()
        )
        metrics = self._compute_streak_metrics(activities)

        if user:
            user.streak = metrics["current"]
        profile.longest_streak = metrics["longest"]
        return user, profile, activities, metrics

    def _aggregate_activity(
        self,
        activities: List[LearnerDailyActivity],
        start_date: date,
        end_date: date,
    ) -> StudyStatsPeriodResponse:
        selected = [
            activity
            for activity in activities
            if start_date <= activity.activity_date <= end_date
        ]
        minutes = sum(int(activity.minutes or 0) for activity in selected)
        return StudyStatsPeriodResponse(
            lessons=sum(int(activity.lessons_completed or 0) for activity in selected),
            hours=self._hours_from_minutes(minutes),
            quizzes=sum(int(activity.quizzes_completed or 0) for activity in selected),
            courses=sum(int(activity.courses_completed or 0) for activity in selected),
        )

    def list_goals(self, db: Session, user_id) -> List[LearningGoal]:
        return (
            db.query(LearningGoal)
            .filter(LearningGoal.user_id == user_id)
            .order_by(LearningGoal.created_at.desc())
            .all()
        )

    def create_goal(self, db: Session, user_id, data: dict) -> LearningGoal:
        goal = LearningGoal(
            user_id=user_id,
            title=data["title"],
            description=data.get("description"),
            goal_type=data["type"],
            target=data["target"],
            current=0,
            unit=data["unit"],
            deadline=data.get("deadline"),
            completed=False,
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal

    def update_goal(self, db: Session, user_id, goal_id, data: dict) -> LearningGoal | None:
        goal = (
            db.query(LearningGoal)
            .filter(LearningGoal.id == goal_id, LearningGoal.user_id == user_id)
            .first()
        )
        if not goal:
            return None

        for field, value in data.items():
            if field == "type":
                setattr(goal, "goal_type", value)
            elif value is not None:
                setattr(goal, field, value)

        goal.completed = bool(data.get("completed", False)) or (goal.current or 0) >= (goal.target or 0)
        db.commit()
        db.refresh(goal)
        return goal

    def delete_goal(self, db: Session, user_id, goal_id) -> bool:
        goal = (
            db.query(LearningGoal)
            .filter(LearningGoal.id == goal_id, LearningGoal.user_id == user_id)
            .first()
        )
        if not goal:
            return False
        db.delete(goal)
        db.commit()
        return True

    def get_study_stats(self, db: Session, user_id) -> StudyStatsResponse:
        _, _, activities, metrics = self._refresh_streak_state(db=db, user_id=user_id)
        today = self._today()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        total_minutes = sum(int(activity.minutes or 0) for activity in activities)

        response = StudyStatsResponse(
            today=StudyStatsTodayResponse(
                lessons=sum(
                    int(activity.lessons_completed or 0)
                    for activity in activities
                    if activity.activity_date == today
                ),
                hours=self._hours_from_minutes(
                    sum(
                        int(activity.minutes or 0)
                        for activity in activities
                        if activity.activity_date == today
                    )
                ),
                quizzes=sum(
                    int(activity.quizzes_completed or 0)
                    for activity in activities
                    if activity.activity_date == today
                ),
            ),
            this_week=self._aggregate_activity(activities, start_of_week, today),
            this_month=self._aggregate_activity(activities, start_of_month, today),
            streak=metrics["current"],
            total_study_time=self._hours_from_minutes(total_minutes),
        )
        db.commit()
        return response

    def get_streak(
        self,
        db: Session,
        user_id,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> LearningStreakResponse:
        _, profile, activities, metrics = self._refresh_streak_state(db=db, user_id=user_id)
        db.commit()
        return LearningStreakResponse(
            current=metrics["current"],
            longest=max(metrics["longest"], int(profile.longest_streak or 0)),
            last_active=metrics["last_active"],
            total_days=metrics["total_days"],
            freezes_available=int(profile.freezes_available or 0),
            calendar=self._build_calendar_map(activities, year=year, month=month),
        )

    def log_activity(self, db: Session, user_id, data: dict) -> LearningStreakResponse:
        activity_date = data.get("activity_date") or self._today()
        today = self._today()
        if activity_date > today:
            raise ValueError("Activity date cannot be in the future")

        activity = (
            db.query(LearnerDailyActivity)
            .filter(
                LearnerDailyActivity.user_id == user_id,
                LearnerDailyActivity.activity_date == activity_date,
            )
            .first()
        )
        if not activity:
            activity = LearnerDailyActivity(user_id=user_id, activity_date=activity_date)
            db.add(activity)

        activity.minutes = int(activity.minutes or 0) + int(data.get("minutes") or 0)
        activity.lessons_completed = int(activity.lessons_completed or 0) + int(data.get("lessons_completed") or 0)
        activity.quizzes_completed = int(activity.quizzes_completed or 0) + int(data.get("quizzes_completed") or 0)
        activity.courses_completed = int(activity.courses_completed or 0) + int(data.get("courses_completed") or 0)

        _, profile, activities, metrics = self._refresh_streak_state(db=db, user_id=user_id)
        db.commit()
        return LearningStreakResponse(
            current=metrics["current"],
            longest=max(metrics["longest"], int(profile.longest_streak or 0)),
            last_active=metrics["last_active"],
            total_days=metrics["total_days"],
            freezes_available=int(profile.freezes_available or 0),
            calendar=self._build_calendar_map(activities),
        )

    def use_streak_freeze(self, db: Session, user_id, activity_date: Optional[date] = None) -> LearningStreakResponse:
        target_date = activity_date or (self._today() - timedelta(days=1))
        if target_date >= self._today():
            raise ValueError("Streak freeze can only be used for past days")

        profile = self._get_or_create_profile(db=db, user_id=user_id)
        if int(profile.freezes_available or 0) <= 0:
            raise ValueError("No streak freezes available")

        activity = (
            db.query(LearnerDailyActivity)
            .filter(
                LearnerDailyActivity.user_id == user_id,
                LearnerDailyActivity.activity_date == target_date,
            )
            .first()
        )
        if not activity:
            activity = LearnerDailyActivity(user_id=user_id, activity_date=target_date)
            db.add(activity)

        if int(activity.minutes or 0) >= ACTIVE_STREAK_MINUTES:
            raise ValueError("This day already qualifies for the streak")

        activity.minutes = ACTIVE_STREAK_MINUTES
        activity.freeze_used = True
        profile.freezes_available = max(int(profile.freezes_available or 0) - 1, 0)

        _, profile, activities, metrics = self._refresh_streak_state(db=db, user_id=user_id)
        db.commit()
        return LearningStreakResponse(
            current=metrics["current"],
            longest=max(metrics["longest"], int(profile.longest_streak or 0)),
            last_active=metrics["last_active"],
            total_days=metrics["total_days"],
            freezes_available=int(profile.freezes_available or 0),
            calendar=self._build_calendar_map(activities),
        )

    def get_progress_dashboard(self, db: Session, user_id) -> ProgressDashboardResponse:
        enrollments = (
            db.query(Enrollment)
            .options(
                joinedload(Enrollment.course)
                .joinedload(Course.sections)
                .joinedload(Section.lessons)
            )
            .filter(Enrollment.user_id == user_id)
            .all()
        )
        course_ids = [enrollment.course_id for enrollment in enrollments]

        progress_records = []
        course_activity = []
        if course_ids:
            progress_records = (
                db.query(LessonProgress)
                .join(Lesson, Lesson.id == LessonProgress.lesson_id)
                .join(Section, Section.id == Lesson.section_id)
                .filter(LessonProgress.user_id == user_id, Section.course_id.in_(course_ids))
                .all()
            )
            course_activity = (
                db.query(CourseActivity)
                .filter(CourseActivity.user_id == user_id, CourseActivity.course_id.in_(course_ids))
                .all()
            )

        progress_by_course: Dict[str, Dict[str, LessonProgress]] = defaultdict(dict)
        completed_progress_records = []
        for record in progress_records:
            course_id = str(record.lesson.section.course_id)
            progress_by_course[course_id][str(record.lesson_id)] = record
            if record.completed or (record.percent or 0) >= 100:
                completed_progress_records.append(record)

        activity_by_course = {str(activity.course_id): activity for activity in course_activity}

        dashboard_enrollments: List[ProgressDashboardEnrollmentResponse] = []
        course_progress_values: List[float] = []
        completed_courses = 0
        in_progress_courses = 0
        user = db.query(User).filter(User.id == user_id).first()

        for enrollment in enrollments:
            course = enrollment.course
            sections = sorted(course.sections or [], key=lambda section: section.order or 0) if course else []
            lessons = [
                lesson
                for section in sections
                for lesson in sorted(section.lessons or [], key=lambda item: item.position or 0)
            ]
            lesson_records = progress_by_course.get(str(enrollment.course_id), {})
            total_lessons = len(lessons)
            course_progress = 0.0
            if total_lessons > 0:
                total_percent = 0.0
                for lesson in lessons:
                    record = lesson_records.get(str(lesson.id))
                    total_percent += min(float(record.percent or 0), 100) if record else 0.0
                course_progress = round(
                    total_percent / total_lessons,
                    1,
                )
            else:
                course_progress = round(float(enrollment.progress or 0), 1)

            is_completed = bool(enrollment.status == "completed" or course_progress >= 100)
            if is_completed:
                completed_courses += 1
            elif course_progress > 0:
                in_progress_courses += 1

            course_progress_values.append(course_progress)
            recent_activity = activity_by_course.get(str(enrollment.course_id))
            dashboard_enrollments.append(
                ProgressDashboardEnrollmentResponse(
                    id=enrollment.id,
                    course_id=enrollment.course_id,
                    course_title=course.title if course else f"Course {enrollment.course_id}",
                    progress=course_progress,
                    completed=is_completed,
                    enrolled_at=enrollment.enrolled_at,
                    last_accessed=(
                        recent_activity.last_accessed_at
                        if recent_activity and recent_activity.last_accessed_at
                        else enrollment.last_accessed or enrollment.enrolled_at
                    ),
                )
            )

        _, profile, activities, metrics = self._refresh_streak_state(db=db, user_id=user_id)

        activity_minutes_total = sum(int(activity.minutes or 0) for activity in activities)
        if activity_minutes_total > 0:
            total_hours_learned = self._hours_from_minutes(activity_minutes_total)
        else:
            total_seconds = (
                db.query(func.coalesce(func.sum(LessonProgress.time_spent_seconds), 0))
                .filter(LessonProgress.user_id == user_id)
                .scalar()
            ) or 0
            total_hours_learned = round(float(total_seconds) / 3600, 1)

        today = self._today()
        start_of_week = today - timedelta(days=today.weekday())
        minutes_by_date = {activity.activity_date: int(activity.minutes or 0) for activity in activities}
        weekly_activity = [
            WeeklyActivityItemResponse(
                day=(start_of_week + timedelta(days=index)).strftime("%a"),
                date=start_of_week + timedelta(days=index),
                minutes=minutes_by_date.get(start_of_week + timedelta(days=index), 0),
            )
            for index in range(7)
        ]

        recent_activity_items: List[RecentActivityItemResponse] = []
        for record in sorted(
            [item for item in completed_progress_records if item.last_seen_at],
            key=lambda item: item.last_seen_at,
            reverse=True,
        )[:5]:
            recent_activity_items.append(
                RecentActivityItemResponse(
                    type="lesson_completed",
                    text=f"Completed lesson: {record.lesson.title}",
                    occurred_at=record.last_seen_at,
                )
            )

        for enrollment in sorted(
            [item for item in enrollments if item.enrolled_at],
            key=lambda item: item.enrolled_at,
            reverse=True,
        )[:5]:
            recent_activity_items.append(
                RecentActivityItemResponse(
                    type="course_enrolled",
                    text=f"Started course: {(enrollment.course.title if enrollment.course else f'Course {enrollment.course_id}')}",
                    occurred_at=enrollment.enrolled_at,
                )
            )

        for activity in sorted(
            [item for item in activities if (item.minutes or 0) > 0],
            key=lambda item: item.activity_date,
            reverse=True,
        )[:5]:
            recent_activity_items.append(
                RecentActivityItemResponse(
                    type="study_logged",
                    text=f"Logged {int(activity.minutes or 0)} minutes of learning",
                    occurred_at=datetime.combine(activity.activity_date, time.min, tzinfo=timezone.utc),
                )
            )

        recent_activity_items = sorted(
            recent_activity_items,
            key=lambda item: item.occurred_at,
            reverse=True,
        )[:10]

        db.commit()
        return ProgressDashboardResponse(
            stats=ProgressDashboardStatsResponse(
                total_courses=len(enrollments),
                completed_courses=completed_courses,
                in_progress_courses=in_progress_courses,
                total_hours_learned=total_hours_learned,
                average_progress=round(
                    sum(course_progress_values) / len(course_progress_values), 1
                ) if course_progress_values else 0,
                current_streak=metrics["current"],
                longest_streak=max(metrics["longest"], int(profile.longest_streak or 0)),
                total_points=int((user.xp if user else 0) or 0),
                certificates_earned=completed_courses,
                lessons_completed=len(completed_progress_records),
            ),
            enrollments=dashboard_enrollments,
            weekly_activity=weekly_activity,
            recent_activity=recent_activity_items,
        )
