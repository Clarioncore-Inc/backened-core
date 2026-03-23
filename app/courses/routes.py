from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.courses.models import Course
from app.courses.schemas import CourseCreate, CourseResponse, CourseUpdate, CourseWithLessons
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
            .filter(Course.is_public.is_(True), Course.status == "published"),
        )

    @router.get("/{course_id}", response_model=CourseWithLessons,
                dependencies=[Depends(get_current_active_user)])
    def get_course(self, course_id: UUID):
        result = service_locator.course_service.get_with_lessons(
            db=self.db, course_id=course_id
        )
        if not result:
            raise HTTPException(status_code=404, detail="Course not found")
        course, lessons = result
        data = CourseWithLessons.model_validate(course)
        data.lessons = [l.__dict__ for l in lessons]
        return data

    @router.post("/", response_model=CourseResponse, status_code=201,
                 dependencies=[Depends(get_current_active_user)])
    def create_course(
        self,
        payload: CourseCreate,
        current_user: User = Depends(get_current_active_user),
    ):
        data = payload.model_dump()
        data["created_by"] = current_user.id
        return service_locator.general_service.create(db=self.db, data=data, model=Course)

    @router.put("/{course_id}", response_model=CourseResponse)
    def update_course(
        self,
        course_id: UUID,
        payload: CourseUpdate,
        current_user: User = Depends(get_current_active_user),
    ):
        course = service_locator.general_service.get(
            db=self.db, key=course_id, model=Course)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        if not service_locator.course_service.is_owner_or_admin(course, current_user):
            raise HTTPException(status_code=403, detail="Forbidden")
        return service_locator.general_service.update_data(
            db=self.db,
            key=course_id,
            data=payload.model_dump(exclude_unset=True),
            model=Course,
        )

    @router.delete("/{course_id}", status_code=204)
    def delete_course(
        self,
        course_id: UUID,
        current_user: User = Depends(get_current_active_user),
    ):
        course = service_locator.general_service.get(
            db=self.db, key=course_id, model=Course)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        if not service_locator.course_service.is_owner_or_admin(course, current_user):
            raise HTTPException(status_code=403, detail="Forbidden")
        service_locator.general_service.delete(
            db=self.db, key=course_id, model=Course)
