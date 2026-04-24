from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session, joinedload

from app.core.dependency_injection import service_locator
from app.accounts.models import User
from app.accounts.schemas import UserResponse
from app.courses.models import Course
from app.courses.schemas import CourseResponse
from app.lessons.models import Section
from app.admin_panel.schemas import (
    PlatformAnalyticsResponse,
    PlatformSettings,
    RoleUpdateRequest,
    SettingsUpdateRequest,
    StatusUpdateRequest,
)
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


@cbv(router)
class AdminView:
    db: Session = Depends(get_db)
    current_user: User = Depends(require_admin)

    @router.get("/users", response_model=Page[UserResponse])
    def list_users(self):
        return paginate(self.db, self.db.query(User))

    @router.get("/courses", response_model=Page[CourseResponse])
    def list_courses(self):
        return paginate(
            self.db,
            self.db.query(Course)
            .options(joinedload(Course.sections).joinedload(Section.lessons)),
        )

    @router.get("/analytics", response_model=PlatformAnalyticsResponse)
    def get_analytics(self):
        return service_locator.admin_service.get_analytics(db=self.db)

    @router.put("/users/{id}/role", response_model=UserResponse)
    def update_role(self, id: UUID, payload: RoleUpdateRequest):
        user = service_locator.admin_service.update_user_role(
            db=self.db, user_id=id, role=payload.role
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @router.put("/users/{id}/status", response_model=UserResponse)
    def update_status(self, id: UUID, payload: StatusUpdateRequest):
        user = service_locator.admin_service.update_user_status(
            db=self.db, user_id=id, suspended=payload.suspended
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @router.get("/settings", response_model=PlatformSettings)
    def get_settings(self):
        return service_locator.admin_service.get_settings()

    @router.put("/settings", response_model=PlatformSettings)
    def update_settings(self, payload: SettingsUpdateRequest):
        return service_locator.admin_service.update_settings(
            updates=payload.model_dump(exclude_unset=True)
        )
