from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.lessons.models import Lesson
from app.lessons.schemas import (
    BookmarkResponse,
    CommentCreate,
    CommentResponse,
    LessonCreate,
    LessonResponse,
)
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User

router = APIRouter(prefix="/lessons", tags=["lessons"])


@cbv(router)
class LessonsView:
    db: Session = Depends(get_db)

    @router.post("/", response_model=LessonResponse, status_code=201)
    def create_lesson(
        self,
        payload: LessonCreate,
        current_user: User = Depends(get_current_active_user),
    ):
        data = payload.model_dump()
        return service_locator.general_service.create(db=self.db, data=data, model=Lesson)

    @router.get("/{lesson_id}", response_model=LessonResponse)
    def get_lesson(self, lesson_id: UUID):
        lesson = service_locator.general_service.get(
            db=self.db, key=lesson_id, model=Lesson)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return lesson

    @router.get("/{lesson_id}/comments", response_model=List[CommentResponse])
    def get_comments(self, lesson_id: UUID):
        return service_locator.lesson_service.get_comments(db=self.db, lesson_id=lesson_id)

    @router.post("/{lesson_id}/like")
    def like_lesson(
        self,
        lesson_id: UUID,
        current_user: User = Depends(get_current_active_user),
    ):
        lesson = service_locator.lesson_service.add_like(
            db=self.db, user_id=current_user.id, lesson_id=lesson_id
        )
        return {"success": True, "likes": lesson.like_count if lesson else 0}

    @router.delete("/{lesson_id}/like")
    def unlike_lesson(
        self,
        lesson_id: UUID,
        current_user: User = Depends(get_current_active_user),
    ):
        lesson = service_locator.lesson_service.remove_like(
            db=self.db, user_id=current_user.id, lesson_id=lesson_id
        )
        return {"success": True, "likes": lesson.like_count if lesson else 0}

    @router.post("/{lesson_id}/bookmark", response_model=BookmarkResponse)
    def bookmark_lesson(
        self,
        lesson_id: UUID,
        current_user: User = Depends(get_current_active_user),
    ):
        return service_locator.lesson_service.add_bookmark(
            db=self.db, user_id=current_user.id, lesson_id=lesson_id
        )


# Bookmarks endpoint (outside /lessons prefix — kept here for service locality)
bookmarks_router = APIRouter(prefix="/bookmarks", tags=["lessons"])


@cbv(bookmarks_router)
class BookmarksView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @bookmarks_router.get("/", response_model=List[BookmarkResponse])
    def get_bookmarks(self):
        return service_locator.lesson_service.get_bookmarks(
            db=self.db, user_id=self.current_user.id
        )


# Comments endpoint (standalone /comments router)
comments_router = APIRouter(prefix="/comments", tags=["lessons"])


@cbv(comments_router)
class CommentsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @comments_router.post("/", response_model=CommentResponse, status_code=201)
    def add_comment(self, payload: CommentCreate):
        data = payload.model_dump()
        return service_locator.lesson_service.add_comment(
            db=self.db, user_id=self.current_user.id, data=data
        )
