from typing import List, Optional
from sqlalchemy.orm import Session
from app.psychologist.models import Booking, PsychologistProfile


class PsychologistService:
    def list_approved(self, db: Session) -> List[PsychologistProfile]:
        return (
            db.query(PsychologistProfile)
            .filter(PsychologistProfile.is_approved == True)
            .all()
        )

    def create_booking(self, db: Session, student_id, data: dict) -> Booking:
        data["student_id"] = student_id
        booking = Booking(**data)
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    def get_user_bookings(self, db: Session, user_id) -> List[Booking]:
        return (
            db.query(Booking)
            .filter(
                (Booking.student_id == user_id) | (Booking.psychologist_id == user_id)
            )
            .all()
        )

    def update_booking(self, db: Session, booking_id, data: dict) -> Optional[Booking]:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return None
        for field, value in data.items():
            setattr(booking, field, value)
        db.commit()
        db.refresh(booking)
        return booking

