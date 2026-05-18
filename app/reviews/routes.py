from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.reviews.schemas import (
    ReviewCreate,
    ReviewResponse,
    ReviewThreadCreate,
    ReviewThreadReactionPayload,
    ReviewThreadResponse,
    ReviewUpdate,
)
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

    @router.put("/{id}", response_model=ReviewResponse)
    def update_review(self, id: UUID, payload: ReviewUpdate):
        try:
            review = service_locator.review_service.update_review(
                db=self.db,
                review_id=id,
                user_id=self.current_user.id,
                data=payload.model_dump(),
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        return review

    @router.delete("/{id}", status_code=204)
    def delete_review(self, id: UUID):
        try:
            deleted = service_locator.review_service.delete_review(
                db=self.db,
                review_id=id,
                user_id=self.current_user.id,
                user_role=self.current_user.role,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))

        if not deleted:
            raise HTTPException(status_code=404, detail="Review not found")

    @router.get("/{id}/threads", response_model=List[ReviewThreadResponse])
    def get_review_threads(self, id: UUID):
        return service_locator.review_service.get_review_threads(db=self.db, review_id=id)

    @router.post("/{id}/threads", response_model=ReviewThreadResponse, status_code=201)
    def create_review_thread(self, id: UUID, payload: ReviewThreadCreate):
        try:
            thread = service_locator.review_service.create_review_thread(
                db=self.db,
                review_id=id,
                user_id=self.current_user.id,
                data=payload.model_dump(),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        if not thread:
            raise HTTPException(status_code=404, detail="Review not found")
        return thread

    @router.post("/threads/{id}/reaction", response_model=ReviewThreadResponse)
    def react_to_review_thread(self, id: UUID, payload: ReviewThreadReactionPayload):
        thread = service_locator.review_service.react_to_review_thread(
            db=self.db,
            thread_id=id,
            user_id=self.current_user.id,
            reaction=payload.reaction.value,
        )
        if not thread:
            raise HTTPException(status_code=404, detail="Review thread not found")
        return thread


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
