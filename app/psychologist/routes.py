from typing import List
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.psychologist.schemas import (
    AcceptInvitePayload,
    BookingCreate,
    BookingNotesPayload,
    BookingNotesResponse,
    BookingResponse,
    BookingTransitionPayload,
    InviteCreate,
    InviteResponse,
    PsychologistProfileResponse,
    PsychologistProfileUpdate,
    PsychologistRegisterCreate,
    PsychologistProfileStatus,
    AvailabilityScheduleResponse,
    AvailabilityScheduleCreate

)
from app.psychologist.models import Booking, SessionType
from app.accounts.schemas import UserResponse
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User
from app.settings import FRONTEND_URL
from app.psychologist.models import PsychologistProfile, AvailabilitySchedule
from app.admin_panel.schemas import SessionTypeResponse
router = APIRouter(prefix="/psychologist", tags=["psychologist"])


@cbv(router)
class PsychologistPublicView:
    db: Session = Depends(get_db)

    @router.post("/register", status_code=status.HTTP_201_CREATED)
    def register_psychologist(self, payload: PsychologistRegisterCreate):
        try:
            result = service_locator.psychologist_service.register_psychologist(
                db=self.db, data=payload.model_dump()
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {
            "user": UserResponse.model_validate(result["user"]),
            "profile": PsychologistProfileResponse.model_validate(result["profile"]),
        }

    @router.post("/accept-invite", status_code=status.HTTP_201_CREATED)
    def accept_invite(self, payload: AcceptInvitePayload):
        try:
            result = service_locator.psychologist_service.accept_invite(
                db=self.db, data=payload.model_dump()
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {
            "user": UserResponse.model_validate(result["user"]),
            "profile": PsychologistProfileResponse.model_validate(result["profile"]),
        }


@cbv(router)
class PsychologistView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @router.get("/list/", response_model=List[PsychologistProfileResponse])
    def list_psychologists(
        self,
        status: PsychologistProfileStatus = None,
        specialization: str = None,
        location: str = None,
        search: str = None,
    ):
        query = self.db.query(PsychologistProfile)

        if status:
            query = query.filter(PsychologistProfile.status == status.value)
        if specialization:
            query = query.filter(
                PsychologistProfile.specialization.ilike(f"%{specialization}%"))
        if location:
            query = query.filter(
                PsychologistProfile.location.ilike(f"%{location}%"))
        if search:
            query = query.filter(PsychologistProfile.bio.ilike(f"%{search}%"))

        return query.all()

    @router.get("/profile", response_model=PsychologistProfileResponse)
    def get_own_profile(self):
        profile = service_locator.psychologist_service.get_profile(
            db=self.db, user_id=self.current_user.id
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile

    @router.put("/profile", response_model=PsychologistProfileResponse)
    def update_own_profile(self, payload: PsychologistProfileUpdate):
        profile = service_locator.psychologist_service.update_profile(
            db=self.db,
            user_id=self.current_user.id,
            data=payload.model_dump(exclude_unset=True, mode="json"),
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile

    @router.post("/admin/invite", response_model=InviteResponse, status_code=201)
    def invite_psychologist(self, payload: InviteCreate):
        if self.current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        invite = service_locator.psychologist_service.create_invite(
            db=self.db,
            admin_id=self.current_user.id,
            email=payload.email,
            frontend_url=FRONTEND_URL,
        )
        return invite

    @router.get("/admin/invites", response_model=List[InviteResponse])
    def list_invites(self):
        if self.current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        return service_locator.psychologist_service.list_invites(db=self.db)

    @router.post("/bookings", response_model=BookingResponse, status_code=201)
    def create_booking(self, payload: BookingCreate):
        data = payload.model_dump()
        return service_locator.psychologist_service.create_booking(
            db=self.db, student_id=self.current_user.id, data=data
        )

    @router.get("/bookings", response_model=List[BookingResponse])
    def list_bookings(self, user_id: UUID):
        if self.current_user.role != "admin" and self.current_user.id != user_id:
            raise HTTPException(
                status_code=403, detail="Not allowed to view these bookings")

        student_bookings = service_locator.general_service.filter_data(
            db=self.db,
            model=Booking,
            filters={"student_id": user_id},
        )
        psychologist_bookings = service_locator.general_service.filter_data(
            db=self.db,
            model=Booking,
            filters={"psychologist_id": user_id},
        )

        return list({booking.id: booking for booking in [*student_bookings, *psychologist_bookings]}.values())

    @router.get("/bookings/{id}/notes", response_model=BookingNotesResponse)
    def get_booking_notes(self, id: UUID):
        booking = service_locator.psychologist_service.get_booking_notes(
            db=self.db,
            booking_id=id,
            psychologist_id=self.current_user.id,
        )
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return BookingNotesResponse(
            **(booking.session_notes or {}),
            updated_at=booking.session_notes_updated_at,
        )

    @router.get("/bookings/available-slots")
    def get_available_slots(
        self,
        booking_date: date = Query(..., description="e.g. 2025-01-30"),
        booking_type: str = Query(default="standard"),
    ):
        slots = service_locator.psychologist_service.get_available_slots(
            db=self.db,
            booking_date=booking_date,
            booking_type=booking_type,
        )
        return {"date": booking_date, "available_slots": slots}

    @router.put("/bookings/{id}/notes", response_model=BookingNotesResponse)
    def update_booking_notes(self, id: UUID, payload: BookingNotesPayload):
        booking = service_locator.psychologist_service.upsert_booking_notes(
            db=self.db,
            booking_id=id,
            psychologist_id=self.current_user.id,
            data=payload.model_dump(exclude_unset=True, mode="json"),
        )
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return BookingNotesResponse(
            **(booking.session_notes or {}),
            updated_at=booking.session_notes_updated_at,
        )

    @router.put("/bookings/{id}", response_model=BookingResponse)
    def update_booking(self, id: UUID, payload: BookingTransitionPayload):
        booking = service_locator.psychologist_service.transition_booking_status(
            db=self.db,
            booking_id=id,
            psychologist_id=self.current_user.id,
            data=payload.model_dump(exclude_unset=True, mode="json"),
        )
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking

    @router.get("/session-types", response_model=List[SessionTypeResponse])
    def list_session_types(self):
        return self.db.query(SessionType).order_by(SessionType.created_at.desc()).all()

    @router.get("/{id}", response_model=PsychologistProfileResponse,
                dependencies=[Depends(get_current_active_user)])
    def get_psychologis(self, id: UUID):
        course = service_locator.general_service.get(
            db=self.db, key=id, model=PsychologistProfile
        )
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course

    @router.put("/{id}", response_model=PsychologistProfileResponse)
    def update(self, id: UUID, payload: PsychologistProfileUpdate):

        data = payload.model_dump(exclude_unset=True, mode="json")

        profile = service_locator.psychologist_service.update_profile_by_id(
            db=self.db,
            profile_id=id,
            data=data,
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile


@cbv(router)
class AvailabilityScheduleView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @router.post("/{id}/availability/", response_model=AvailabilityScheduleResponse)
    def create_or_update(self, id: UUID, payload: AvailabilityScheduleCreate):

        id = service_locator.psychologist_service.resolve_user_id(self.db, id)

        existing = self.db.query(AvailabilitySchedule).filter(
            AvailabilitySchedule.psychologist_id == id
        ).first()

        if existing:
            return service_locator.general_service.update_data(
                db=self.db,
                key=existing.id,
                data={"schedule": payload.model_dump(mode="json")},
                model=AvailabilitySchedule,
            )

        return service_locator.general_service.create(
            db=self.db,
            data={"psychologist_id": id,
                  "schedule": payload.model_dump(mode="json")},
            model=AvailabilitySchedule,
        )

    @router.get("/{id}/availability/", response_model=AvailabilityScheduleResponse)
    def get(self, id: UUID):

        id = service_locator.psychologist_service.resolve_user_id(self.db, id)

        schedule = self.db.query(AvailabilitySchedule).filter(
            AvailabilitySchedule.psychologist_id == id,
        ).first()
        if not schedule:
            raise HTTPException(
                status_code=404, detail="Availability schedule not found")
        return schedule
