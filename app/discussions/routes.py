from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.accounts.models import User
from app.authentication.utils import get_current_active_user
from app.core.dependency_injection import service_locator
from app.dependencies import get_db
from app.discussions.schemas import (
    DiscussionCategoryEnum,
    DiscussionCreate,
    DiscussionPostResponse,
    DiscussionReplyCreate,
    DiscussionReplyResponse,
)

router = APIRouter(prefix="/discussions", tags=["discussions"])


@cbv(router)
class DiscussionsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @router.get("/", response_model=List[DiscussionPostResponse])
    def list_posts(self, category: Optional[DiscussionCategoryEnum] = None):
        return service_locator.discussion_service.list_posts(
            db=self.db,
            category=category.value if category else None,
        )

    @router.post("/", response_model=DiscussionPostResponse, status_code=201)
    def create_post(self, payload: DiscussionCreate):
        return service_locator.discussion_service.create_post(
            db=self.db,
            user_id=self.current_user.id,
            data=payload.model_dump(mode="json"),
        )

    @router.get("/{id}", response_model=DiscussionPostResponse)
    def get_post(self, id: UUID):
        post = service_locator.discussion_service.get_post(db=self.db, post_id=id)
        if not post:
            raise HTTPException(status_code=404, detail="Discussion post not found")
        return post

    @router.post("/{id}/replies", response_model=DiscussionReplyResponse, status_code=201)
    def create_reply(self, id: UUID, payload: DiscussionReplyCreate):
        try:
            reply = service_locator.discussion_service.create_reply(
                db=self.db,
                post_id=id,
                user_id=self.current_user.id,
                data=payload.model_dump(mode="json"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        if not reply:
            raise HTTPException(status_code=404, detail="Discussion post not found")
        return reply

    @router.post("/{id}/like", response_model=DiscussionPostResponse)
    def toggle_like(self, id: UUID):
        post = service_locator.discussion_service.toggle_like(
            db=self.db, post_id=id, user_id=self.current_user.id
        )
        if not post:
            raise HTTPException(status_code=404, detail="Discussion post not found")
        return post