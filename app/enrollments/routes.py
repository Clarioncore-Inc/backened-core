from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.enrollments.schemas import EnrollmentCreate, EnrollmentResponse
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@cbv(router)
class EnrollmentsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @router.get("/", response_model=List[EnrollmentResponse])
    def list_enrollments(self):
        return service_locator.enrollment_service.get_user_enrollments(
            db=self.db, user_id=self.current_user.id
        )

    @router.post("/", response_model=EnrollmentResponse, status_code=201)
    def enroll(self, payload: EnrollmentCreate):
        return service_locator.enrollment_service.enroll(
            db=self.db,
            user_id=self.current_user.id,
            course_id=payload.course_id,
        )

    @router.delete("/{enrollment_id}", status_code=204)
    def unenroll(self, enrollment_id: UUID):
        success = service_locator.enrollment_service.unenroll(
            db=self.db,
            enrollment_id=enrollment_id,
            user_id=self.current_user.id,
        )
        if not success:
            raise HTTPException(status_code=404, detail="Enrollment not found")

    @router.get("/course/{course_id}", response_model=List[EnrollmentResponse])
    def list_course_enrollments(self, course_id: UUID):
        if self.current_user.role not in ("admin", "creator", "instructor"):
            raise HTTPException(status_code=403, detail="Forbidden")
        return service_locator.enrollment_service.get_course_enrollments(
            db=self.db, course_id=course_id
        )
