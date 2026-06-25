import re
from typing import List, Optional
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
from app.admin_panel.models import GeniusProfile, _iq_label, _iq_note
from app.admin_panel.schemas import (
    GeniusCreate,
    GeniusListResponse,
    GeniusResponse,
    GeniusStatusUpdate,
    GeniusUpdate,
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
from app.general.schemas import AppSettingsResponse, AppSettingsUpdateRequest

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/app-settings/public", response_model=AppSettingsResponse)
def get_public_app_settings(db: Session = Depends(get_db)):
    return service_locator.general_service.get_app_settings(db=db)


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

    @router.get("/app-settings", response_model=AppSettingsResponse)
    def get_app_settings(self):
        return service_locator.general_service.get_app_settings(db=self.db)

    @router.put("/app-settings", response_model=AppSettingsResponse)
    def update_app_settings(self, payload: AppSettingsUpdateRequest):
        return service_locator.general_service.update_app_settings(
            db=self.db,
            updates=payload.model_dump(exclude_unset=True),
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

    # ── Genius Profiles ────────────────────────────────────────────────────────

    @router.get("/genius-profiles", response_model=GeniusListResponse)
    def list_genius_profiles(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        profile_type: Optional[str] = None,
    ):
        q = self.db.query(GeniusProfile)
        if status:
            q = q.filter(GeniusProfile.publication_status == status)
        if profile_type:
            q = q.filter(GeniusProfile.profile_type == profile_type)
        if query:
            search = f"%{query}%"
            q = q.filter(
                GeniusProfile.full_name.ilike(search)
                | GeniusProfile.short_description.ilike(search)
            )
        items = q.all()
        return {"items": items, "total": len(items)}

    @router.post("/genius-profiles", response_model=GeniusResponse, status_code=status.HTTP_201_CREATED)
    def create_genius_profile(self, payload: GeniusCreate):
        data = payload.model_dump()

        genius_id = data.get("id")
        if genius_id:
            if service_locator.general_service.get(self.db, genius_id, GeniusProfile):
                raise HTTPException(status_code=409, detail="A profile with this ID already exists")
        else:
            base = re.sub(r"[^a-z0-9\s-]", "", data["full_name"].lower())
            base = re.sub(r"\s+", "-", base.strip())
            candidate, counter = base, 2
            while self.db.query(GeniusProfile).filter(GeniusProfile.id == candidate).first():
                candidate = f"{base}-{counter}"
                counter += 1
            genius_id = candidate

        data["id"] = genius_id
        data["slug"] = genius_id
        data["iq_score_label"] = _iq_label(data.get("iq_score"), data.get("profile_type", "historical"))
        data["iq_score_note"] = _iq_note(data.get("iq_score"))
        if not data.get("editorial_note"):
            data["editorial_note"] = "Editorial profile for learning inspiration. Intelligence labels are contextual and should be read as estimates where shown."

        return service_locator.general_service.create(self.db, data, GeniusProfile)

    @router.get("/genius-profiles/{genius_id}", response_model=GeniusResponse)
    def get_genius_profile(self, genius_id: str):
        profile = service_locator.general_service.get(self.db, genius_id, GeniusProfile)
        if not profile:
            raise HTTPException(status_code=404, detail="Genius profile not found")
        return profile

    @router.put("/genius-profiles/{genius_id}", response_model=GeniusResponse)
    def update_genius_profile(self, genius_id: str, payload: GeniusUpdate):
        data = payload.model_dump(exclude_unset=True)

        if "iq_score" in data or "profile_type" in data:
            existing = service_locator.general_service.get(self.db, genius_id, GeniusProfile)
            if not existing:
                raise HTTPException(status_code=404, detail="Genius profile not found")
            iq = data.get("iq_score", existing.iq_score)
            pt = data.get("profile_type", existing.profile_type)
            data["iq_score_label"] = _iq_label(iq, pt)
            data["iq_score_note"] = _iq_note(iq)

        updated = service_locator.general_service.update_data(
            self.db, genius_id, data, GeniusProfile
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Genius profile not found")
        return updated

    @router.patch("/genius-profiles/{genius_id}/status", response_model=GeniusResponse)
    def update_genius_status(self, genius_id: str, payload: GeniusStatusUpdate):
        updated = service_locator.general_service.update_data(
            self.db, genius_id, {"publication_status": payload.publication_status}, GeniusProfile
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Genius profile not found")
        return updated

    @router.delete("/genius-profiles/{genius_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_genius_profile(self, genius_id: str):
        if not service_locator.general_service.delete(self.db, genius_id, GeniusProfile):
            raise HTTPException(status_code=404, detail="Genius profile not found")


# ── Public genius routes (no auth required) ────────────────────────────────────

public_genius_router = APIRouter(prefix="/genius-profiles", tags=["genius"])


@public_genius_router.get("", response_model=GeniusListResponse)
def list_published_genius_profiles(
    query: Optional[str] = None,
    era: Optional[str] = None,
    profile_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(GeniusProfile).filter(GeniusProfile.publication_status == "published")
    if era:
        q = q.filter(GeniusProfile.era == era)
    if profile_type:
        q = q.filter(GeniusProfile.profile_type == profile_type)
    if query:
        search = f"%{query}%"
        q = q.filter(
            GeniusProfile.full_name.ilike(search)
            | GeniusProfile.short_description.ilike(search)
        )
    items = q.all()
    return {"items": items, "total": len(items)}


@public_genius_router.get("/{genius_id}", response_model=GeniusResponse)
def get_published_genius_profile(genius_id: str, db: Session = Depends(get_db)):
    profile = (
        db.query(GeniusProfile)
        .filter(GeniusProfile.id == genius_id, GeniusProfile.publication_status == "published")
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Genius profile not found")
    return profile
