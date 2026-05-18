from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.accounts.models import User
from app.authentication.utils import get_current_active_user
from app.core.dependency_injection import service_locator
from app.dependencies import get_db
from app.learner.schemas import (
    LearningActivityLog,
    LearningGoalCreate,
    LearningGoalResponse,
    LearningGoalUpdate,
    LearningStreakResponse,
    ProgressDashboardResponse,
    StudyStatsResponse,
    UseStreakFreezePayload,
)

router = APIRouter(prefix="/learner", tags=["learner"])


@cbv(router)
class LearnerView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @router.get("/goals", response_model=List[LearningGoalResponse])
    def list_goals(self):
        return service_locator.learner_service.list_goals(
            db=self.db, user_id=self.current_user.id
        )

    @router.post("/goals", response_model=LearningGoalResponse, status_code=201)
    def create_goal(self, payload: LearningGoalCreate):
        return service_locator.learner_service.create_goal(
            db=self.db,
            user_id=self.current_user.id,
            data=payload.model_dump(mode="json"),
        )

    @router.put("/goals/{id}", response_model=LearningGoalResponse)
    def update_goal(self, id: UUID, payload: LearningGoalUpdate):
        goal = service_locator.learner_service.update_goal(
            db=self.db,
            user_id=self.current_user.id,
            goal_id=id,
            data=payload.model_dump(mode="json", exclude_unset=True),
        )
        if not goal:
            raise HTTPException(status_code=404, detail="Learning goal not found")
        return goal

    @router.delete("/goals/{id}", status_code=204)
    def delete_goal(self, id: UUID):
        deleted = service_locator.learner_service.delete_goal(
            db=self.db, user_id=self.current_user.id, goal_id=id
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Learning goal not found")

    @router.get("/study-stats", response_model=StudyStatsResponse)
    def get_study_stats(self):
        return service_locator.learner_service.get_study_stats(
            db=self.db, user_id=self.current_user.id
        )

    @router.get("/streak", response_model=LearningStreakResponse)
    def get_streak(self, year: Optional[int] = None, month: Optional[int] = None):
        return service_locator.learner_service.get_streak(
            db=self.db,
            user_id=self.current_user.id,
            year=year,
            month=month,
        )

    @router.post("/streak/log-activity", response_model=LearningStreakResponse)
    def log_activity(self, payload: LearningActivityLog):
        try:
            return service_locator.learner_service.log_activity(
                db=self.db,
                user_id=self.current_user.id,
                data=payload.model_dump(mode="json"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @router.post("/streak/use-freeze", response_model=LearningStreakResponse)
    def use_streak_freeze(self, payload: UseStreakFreezePayload):
        try:
            return service_locator.learner_service.use_streak_freeze(
                db=self.db,
                user_id=self.current_user.id,
                activity_date=payload.activity_date,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @router.get("/progress-dashboard", response_model=ProgressDashboardResponse)
    def get_progress_dashboard(self):
        return service_locator.learner_service.get_progress_dashboard(
            db=self.db, user_id=self.current_user.id
        )
