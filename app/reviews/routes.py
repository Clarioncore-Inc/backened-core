from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.reviews.schemas import ReviewCreate, ReviewResponse
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User

router = APIRouter(prefix="/reviews", tags=["reviews"])

# Course reviews sub-route (also registered in courses router via main.py)
course_reviews_router = APIRouter(tags=["reviews"])


@cbv(router)
class ReviewsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @router.post("/", response_model=ReviewResponse, status_code=201)
    def create_review(self, payload: ReviewCreate):
        data = payload.model_dump()
        return service_locator.review_service.create_review(
            db=self.db, user_id=self.current_user.id, data=data
        )


@cbv(course_reviews_router)
class CourseReviewsView:
    db: Session = Depends(get_db)

    @course_reviews_router.get(
        "/courses/{id}/reviews", response_model=List[ReviewResponse]
    )
    def get_course_reviews(self, id: UUID):
        return service_locator.review_service.get_course_reviews(
            db=self.db, course_id=id
        )
