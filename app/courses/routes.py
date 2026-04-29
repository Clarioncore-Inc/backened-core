from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from app.core.dependency_injection import service_locator
from app.courses.models import Course, CourseCollaborator, CourseComment, CourseHistory
from app.lessons.models import Section
from app.courses.schemas import (
    CourseBulkCreate,
    CourseBulkUpdate,
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    CourseWithSections,
    CourseCommentCreate,
    CourseCommentResponse,
    CourseHistoryResponse
)
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User


router = APIRouter(prefix="/courses", tags=["courses"])


@cbv(router)
class CoursesView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @router.get("/", response_model=Page[CourseResponse])
    def list_courses(self):
        query = (
            self.db.query(Course)
            .options(joinedload(Course.sections).joinedload(Section.lessons))
            .outerjoin(CourseCollaborator, CourseCollaborator.course_id == Course.id)
            .filter(
                or_(
                    and_(Course.is_public.is_(True),
                         Course.status == "published"),
                    CourseCollaborator.user_id == self.current_user.id,
                )
            )
        )
        return paginate(self.db, query)

    @router.post("/bulk", response_model=CourseWithSections, status_code=201)
    def create_course_bulk(
        self,
        payload: CourseBulkCreate,
    ):
        data = payload.model_dump()
        data["created_by"] = self.current_user.id
        sections_data = data.pop("sections", [])
        return service_locator.course_service.create_bulk(
            db=self.db, course_data=data, sections_data=sections_data
        )

    @router.get("/{id}", response_model=CourseWithSections,
                dependencies=[Depends(get_current_active_user)])
    def get_course(self, id: UUID):
        course = service_locator.course_service.get_course_detail(
            db=self.db, course_id=id
        )
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course

    @router.post("/", response_model=CourseWithSections, status_code=201)
    def create_course(
        self,
        payload: CourseBulkCreate,
    ):
        data = payload.model_dump()
        data["created_by"] = self.current_user.id
        sections_data = data.pop("sections", [])
        return service_locator.course_service.create_bulk(
            db=self.db, course_data=data, sections_data=sections_data
        )

    @router.put("/{id}", response_model=CourseResponse)
    def update_course(
        self,
        id: UUID,
        payload: CourseUpdate,
    ):
        course = service_locator.general_service.get(
            db=self.db, key=id, model=Course)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        if not service_locator.course_service.is_owner_or_admin(course, self.current_user):
            raise HTTPException(status_code=403, detail="Forbidden")

        data = payload.model_dump(exclude_unset=True)

        service_locator.course_service.track_course_changes(
            self.db, course, data, self.current_user.id)

        return service_locator.general_service.update_data(
            db=self.db,
            key=id,
            data=data,
            model=Course,
        )

    @router.put("/{id}/bulk", response_model=CourseWithSections)
    def update_course_bulk(
        self,
        id: UUID,
        payload: CourseBulkUpdate,
        current_user: User = Depends(get_current_active_user),
    ):
        course = service_locator.general_service.get(
            db=self.db, key=id, model=Course)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        if not service_locator.course_service.is_owner_or_admin(course, current_user):
            raise HTTPException(status_code=403, detail="Forbidden")
        data = payload.model_dump(exclude_unset=True)
        result = service_locator.course_service.update_bulk(
            db=self.db, course_id=id, course_data=data
        )
        if not result:
            raise HTTPException(status_code=404, detail="Course not found")
        return result

    @router.delete("/{id}", status_code=204)
    def delete_course(
        self,
        id: UUID,
        current_user: User = Depends(get_current_active_user),
    ):
        course = service_locator.general_service.get(
            db=self.db, key=id, model=Course)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        if not service_locator.course_service.is_owner_or_admin(course, current_user):
            raise HTTPException(status_code=403, detail="Forbidden")
        service_locator.general_service.delete(
            db=self.db, key=id, model=Course)

    @router.get("/{id}/history", response_model=Page[CourseHistoryResponse])
    def get_course_history(self, id: UUID):
        query = self.db.query(CourseHistory).filter(
            CourseHistory.course_id == id
        ).order_by(CourseHistory.created_at.desc())
        return paginate(self.db, query)

    # Course comments

    @router.get("/{id}/comments/", response_model=Page[CourseCommentResponse])
    def list_course_comments(self, id: UUID):
        query = self.db.query(CourseComment).filter(
            CourseComment.course_id == id,
            CourseComment.parent_id.is_(None)
        )
        return paginate(self.db, query)

    @router.put("/comments/{id}/", response_model=CourseCommentResponse)
    def update_course_comment(self, id: UUID, payload: CourseCommentCreate):

        comment = service_locator.general_service.update_data(
            db=self.db,
            key=id,
            data=payload.model_dump(exclude_unset=True),
            model=CourseComment,
        )
        if not comment:
            raise HTTPException(
                status_code=404, detail="Course comment not found")
        return comment

    @router.delete("/comments/{id}/", status_code=204)
    def delete_course_comment(self, id: UUID):

        deleted = service_locator.general_service.delete(
            db=self.db, key=id, model=CourseComment)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Course comment not found")

    @router.post("/{id}/comments/", response_model=CourseCommentResponse, status_code=201)
    def create_course_comment(self, id: UUID, payload: CourseCommentCreate):
        data = payload.model_dump()
        data["user_id"] = self.current_user.id
        data["course_id"] = id
        return service_locator.general_service.create(db=self.db, data=data, model=CourseComment)
