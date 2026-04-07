from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.lessons.models import Lesson, Section
from app.attachment.models import Attachment
from app.lessons.schemas import (
    BookmarkResponse,
    CommentCreate,
    CommentResponse,
    LessonCreate,
    LessonResponse,
    LessonUpdate,
    SectionCreate,
    SectionResponse,
    SectionUpdate,
)
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User

sections_router = APIRouter(prefix="/sections", tags=["sections"])


@cbv(sections_router)
class SectionsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @sections_router.post("/", response_model=SectionResponse, status_code=201)
    def create_section(self, payload: SectionCreate):
        data = payload.model_dump(exclude={"attachment_ids"})
        section = service_locator.general_service.create(db=self.db, data=data, model=Section)
        if payload.attachment_ids:
            section.attachments = self.db.query(Attachment).filter(Attachment.id.in_(payload.attachment_ids)).all()
            self.db.commit()
            self.db.refresh(section)
        return section

    @sections_router.get("/{id}", response_model=SectionResponse)
    def get_section(self, id: UUID):
        section = service_locator.lesson_service.get_section_with_lessons(
            db=self.db, section_id=id
        )
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        return section

    @sections_router.put("/{id}", response_model=SectionResponse)
    def update_section(self, id: UUID, payload: SectionUpdate):
        data = payload.model_dump(exclude_unset=True, exclude={"attachment_ids"})
        section = service_locator.general_service.update_data(
            db=self.db, key=id, data=data, model=Section
        )
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        if payload.attachment_ids is not None:
            section.attachments = self.db.query(Attachment).filter(Attachment.id.in_(payload.attachment_ids)).all()
            self.db.commit()
            self.db.refresh(section)
        return section

    @sections_router.delete("/{id}", status_code=204)
    def delete_section(self, id: UUID):
        section = service_locator.general_service.get(
            db=self.db, key=id, model=Section)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        service_locator.general_service.delete(
            db=self.db, key=id, model=Section)


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

    @router.get("/{id}", response_model=LessonResponse)
    def get_lesson(self, id: UUID):
        lesson = service_locator.general_service.get(
            db=self.db, key=id, model=Lesson)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return lesson

    @router.put("/{id}", response_model=LessonResponse)
    def update_lesson(
        self,
        id: UUID,
        payload: LessonUpdate,
        current_user: User = Depends(get_current_active_user),
    ):
        lesson = service_locator.general_service.update_data(
            db=self.db, key=id, data=payload.model_dump(exclude_unset=True), model=Lesson
        )
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return lesson

    @router.delete("/{id}", status_code=204)
    def delete_lesson(
        self,
        id: UUID,
        current_user: User = Depends(get_current_active_user),
    ):
        lesson = service_locator.general_service.get(
            db=self.db, key=id, model=Lesson)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        service_locator.general_service.delete(
            db=self.db, key=id, model=Lesson)

    @router.get("/{id}/comments", response_model=List[CommentResponse])
    def get_comments(self, id: UUID):
        return service_locator.lesson_service.get_comments(db=self.db, lesson_id=id)

    @router.post("/{id}/like")
    def like_lesson(self, id: UUID, current_user: User = Depends(get_current_active_user)):
        lesson = service_locator.lesson_service.add_like(
            db=self.db, user_id=current_user.id, lesson_id=id
        )
        return {"success": True, "likes": lesson.like_count if lesson else 0}

    @router.delete("/{id}/like")
    def unlike_lesson(self, id: UUID, current_user: User = Depends(get_current_active_user)):
        lesson = service_locator.lesson_service.remove_like(
            db=self.db, user_id=current_user.id, lesson_id=id
        )
        return {"success": True, "likes": lesson.like_count if lesson else 0}

    @router.post("/{id}/bookmark", response_model=BookmarkResponse)
    def bookmark_lesson(self, id: UUID, current_user: User = Depends(get_current_active_user)):
        return service_locator.lesson_service.add_bookmark(
            db=self.db, user_id=current_user.id, lesson_id=id
        )


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
