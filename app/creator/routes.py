from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.courses.schemas import CourseResponse
from app.enrollments.schemas import EnrollmentResponse
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User

router = APIRouter(prefix="/creator", tags=["creator"])


@cbv(router)
class CreatorView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @router.get("/courses", response_model=List[CourseResponse])
    def list_my_courses(self):
        return service_locator.course_service.get_creator_courses(
            db=self.db, user_id=self.current_user.id
        )

    @router.get("/courses/{id}/subscribers", response_model=List[EnrollmentResponse])
    def get_subscribers(self, id: UUID):
        return service_locator.enrollment_service.get_course_enrollments(
            db=self.db, course_id=id
        )

    @router.get("/courses/{id}/analytics")
    def get_analytics(self, id: UUID) -> Dict[str, Any]:
        enrollments = service_locator.enrollment_service.get_course_enrollments(
            db=self.db, course_id=id
        )
        from app.payments.models import Payment
        payments = (
            self.db.query(Payment)
            .filter(
                Payment.course_id == id,
                Payment.status == "completed",
            )
            .all()
        )
        total_revenue = sum(float(p.amount) for p in payments)
        return {
            "analytics": {
                "total_students": len(enrollments),
                "total_revenue": total_revenue,
                "currency": "USD",
            }
        }

    @router.get("/earnings")
    def get_earnings(self) -> Dict[str, Any]:
        earnings = service_locator.payment_service.get_creator_earnings(
            db=self.db, creator_id=self.current_user.id
        )
        return {"earnings": earnings}
