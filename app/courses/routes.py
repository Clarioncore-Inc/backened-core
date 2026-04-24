from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session, joinedload

from app.core.dependency_injection import service_locator
from app.courses.models import Course
from app.lessons.models import Section
from app.courses.schemas import (
    CourseBulkCreate,
    CourseBulkUpdate,
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    CourseWithSections,
)
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User

router = APIRouter(prefix="/courses", tags=["courses"])


@cbv(router)
class CoursesView:
    db: Session = Depends(get_db)

    @router.get("/", response_model=Page[CourseResponse],
                dependencies=[Depends(get_current_active_user)])
    def list_courses(self):
        return paginate(
            self.db,
            self.db.query(Course)
            .options(joinedload(Course.sections).joinedload(Section.lessons))
            .filter(Course.is_public.is_(True), Course.status == "published"),
        )

    @router.post("/bulk", response_model=CourseWithSections, status_code=201)
    def create_course_bulk(
        self,
        payload: CourseBulkCreate,
        current_user: User = Depends(get_current_active_user),
    ):
        data = payload.model_dump()
        data["created_by"] = current_user.id
        sections_data = data.pop("sections", [])
        return service_locator.course_service.create_bulk(
            db=self.db, course_data=data, sections_data=sections_data
        )

    @router.get("/{id}", response_model=CourseWithSections,
                dependencies=[Depends(get_current_active_user)])
    def get_course(self, id: UUID):
        course = service_locator.course_service.get_with_sections(
            db=self.db, course_id=id
        )
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course

    @router.post("/", response_model=CourseResponse, status_code=201)
    def create_course(
        self,
        payload: CourseCreate,
        current_user: User = Depends(get_current_active_user),
    ):
        data = payload.model_dump()
        data["created_by"] = current_user.id
        return service_locator.general_service.create(db=self.db, data=data, model=Course)

    @router.put("/{id}", response_model=CourseResponse)
    def update_course(
        self,
        id: UUID,
        payload: CourseUpdate,
        current_user: User = Depends(get_current_active_user),
    ):
        course = service_locator.general_service.get(
            db=self.db, key=id, model=Course)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        if not service_locator.course_service.is_owner_or_admin(course, current_user):
            raise HTTPException(status_code=403, detail="Forbidden")
        return service_locator.general_service.update_data(
            db=self.db,
            key=id,
            data=payload.model_dump(exclude_unset=True),
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
