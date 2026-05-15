from typing import List
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
from app.psychologist.models import MeetingConfig, SessionType
from app.admin_panel.schemas import (
    MeetingConfigResponse,
    MeetingConfigUpsert,
    PlatformAnalyticsResponse,
    PlatformSettings,
    RoleUpdateRequest,
    SessionTypeCreate,
    SessionTypeResponse,
    SessionTypeUpdate,
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
    def list_courses(
        self,
        status: str = None,
        is_public: bool = None,
        search: str = None,
    ):
        query = (
            self.db.query(Course)
            .options(joinedload(Course.sections).joinedload(Section.lessons))
        )

        if status:
            query = query.filter(Course.status == status)
        if is_public is not None:
            query = query.filter(Course.is_public.is_(is_public))
        if search:
            query = query.filter(Course.title.ilike(f"%{search}%"))

        return paginate(self.db, query)

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

    # ── Session Types ──────────────────────────────────────────────────────────

    @router.post("/session-types", response_model=SessionTypeResponse, status_code=status.HTTP_201_CREATED)
    def create_session_type(self, payload: SessionTypeCreate):
        session_type = SessionType(
            name=payload.name,
            price=payload.price,
            description=payload.description,
        )
        self.db.add(session_type)
        self.db.commit()
        self.db.refresh(session_type)
        return session_type

    @router.get("/session-types", response_model=List[SessionTypeResponse])
    def list_session_types(self):
        return self.db.query(SessionType).order_by(SessionType.created_at.desc()).all()

    @router.get("/session-types/{id}", response_model=SessionTypeResponse)
    def get_session_type(self, id: UUID):
        session_type = self.db.query(SessionType).filter(SessionType.id == id).first()
        if not session_type:
            raise HTTPException(status_code=404, detail="Session type not found")
        return session_type

    @router.put("/session-types/{id}", response_model=SessionTypeResponse)
    def update_session_type(self, id: UUID, payload: SessionTypeUpdate):
        session_type = self.db.query(SessionType).filter(SessionType.id == id).first()
        if not session_type:
            raise HTTPException(status_code=404, detail="Session type not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(session_type, field, value)
        self.db.commit()
        self.db.refresh(session_type)
        return session_type

    @router.delete("/session-types/{id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_session_type(self, id: UUID):
        session_type = self.db.query(SessionType).filter(SessionType.id == id).first()
        if not session_type:
            raise HTTPException(status_code=404, detail="Session type not found")
        self.db.delete(session_type)
        self.db.commit()

    # ── Meeting Config ─────────────────────────────────────────────────────────

    @router.get("/meeting-config", response_model=MeetingConfigResponse)
    def get_meeting_config(self):
        config = self.db.query(MeetingConfig).first()
        if not config:
            raise HTTPException(status_code=404, detail="Meeting config not set")
        return config

    @router.put("/meeting-config", response_model=MeetingConfigResponse)
    def upsert_meeting_config(self, payload: MeetingConfigUpsert):
        config = self.db.query(MeetingConfig).first()
        if config:
            config.name = payload.name
            config.link = payload.link
            config.password = payload.password
        else:
            config = MeetingConfig(
                name=payload.name,
                link=payload.link,
                password=payload.password,
            )
            self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config
