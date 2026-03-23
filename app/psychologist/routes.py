from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.psychologist.schemas import (
    BookingCreate,
    BookingResponse,
    BookingUpdate,
    PsychologistProfileResponse,
)
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User

router = APIRouter(prefix="/psychologist", tags=["psychologist"])


@cbv(router)
class PsychologistView:
    db: Session = Depends(get_db)

    @router.get("/list", response_model=List[PsychologistProfileResponse])
    def list_psychologists(self):
        return service_locator.psychologist_service.list_approved(db=self.db)

    @router.post(
        "/bookings",
        response_model=BookingResponse,
        status_code=201,
        dependencies=[Depends(get_current_active_user)],
    )
    def create_booking(
        self,
        payload: BookingCreate,
        current_user: User = Depends(get_current_active_user),
    ):
        data = payload.model_dump()
        return service_locator.psychologist_service.create_booking(
            db=self.db, student_id=current_user.id, data=data
        )

    @router.get(
        "/bookings",
        response_model=List[BookingResponse],
        dependencies=[Depends(get_current_active_user)],
    )
    def list_bookings(self, current_user: User = Depends(get_current_active_user)):
        return service_locator.psychologist_service.get_user_bookings(
            db=self.db, user_id=current_user.id
        )

    @router.put(
        "/bookings/{booking_id}",
        response_model=BookingResponse,
        dependencies=[Depends(get_current_active_user)],
    )
    def update_booking(
        self,
        booking_id: UUID,
        payload: BookingUpdate,
        current_user: User = Depends(get_current_active_user),
    ):
        booking = service_locator.psychologist_service.update_booking(
            db=self.db,
            booking_id=booking_id,
            data=payload.model_dump(exclude_unset=True),
        )
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking

