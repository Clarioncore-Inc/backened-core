from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.psychologist.schemas import (
    AcceptInvitePayload,
    BookingCreate,
    BookingResponse,
    BookingUpdate,
    InviteCreate,
    InviteResponse,
    PsychologistProfileResponse,
    PsychologistProfileUpdate,
    PsychologistRegisterCreate,
)
from app.accounts.schemas import UserResponse
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User
from app.settings import FRONTEND_URL

router = APIRouter(prefix="/psychologist", tags=["psychologist"])


@cbv(router)
class PsychologistView:
    db: Session = Depends(get_db)

    @router.get("/list", response_model=List[PsychologistProfileResponse])
    def list_psychologists(self):
        return service_locator.psychologist_service.list_approved(db=self.db)

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

    @router.get("/profile", response_model=PsychologistProfileResponse)
    def get_own_profile(self, current_user: User = Depends(get_current_active_user)):
        profile = service_locator.psychologist_service.get_profile(
            db=self.db, user_id=current_user.id
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile

    @router.put("/profile", response_model=PsychologistProfileResponse)
    def update_own_profile(
        self,
        payload: PsychologistProfileUpdate,
        current_user: User = Depends(get_current_active_user),
    ):
        profile = service_locator.psychologist_service.update_profile(
            db=self.db,
            user_id=current_user.id,
            data=payload.model_dump(exclude_unset=True),
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile

    @router.post("/admin/invite", response_model=InviteResponse, status_code=201)
    def invite_psychologist(
        self,
        payload: InviteCreate,
        current_user: User = Depends(get_current_active_user),
    ):
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        invite = service_locator.psychologist_service.create_invite(
            db=self.db,
            admin_id=current_user.id,
            email=payload.email,
            frontend_url=FRONTEND_URL,
        )
        return invite

    @router.get("/admin/invites", response_model=List[InviteResponse])
    def list_invites(self, current_user: User = Depends(get_current_active_user)):
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        return service_locator.psychologist_service.list_invites(db=self.db)

    @router.post("/bookings", response_model=BookingResponse, status_code=201)
    def create_booking(
        self,
        payload: BookingCreate,
        current_user: User = Depends(get_current_active_user),
    ):
        data = payload.model_dump()
        return service_locator.psychologist_service.create_booking(
            db=self.db, student_id=current_user.id, data=data
        )

    @router.get("/bookings", response_model=List[BookingResponse])
    def list_bookings(self, current_user: User = Depends(get_current_active_user)):
        return service_locator.psychologist_service.get_user_bookings(
            db=self.db, user_id=current_user.id
        )

    @router.put("/bookings/{id}", response_model=BookingResponse)
    def update_booking(
        self,
        id: UUID,
        payload: BookingUpdate,
        current_user: User = Depends(get_current_active_user),
    ):
        booking = service_locator.psychologist_service.update_booking(
            db=self.db,
            booking_id=id,
            data=payload.model_dump(exclude_unset=True),
        )
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking
