import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.psychologist.models import Booking, PsychologistInvite, PsychologistProfile


class PsychologistService:
    def list_approved(self, db: Session) -> List[PsychologistProfile]:
        return (
            db.query(PsychologistProfile)
            .filter(PsychologistProfile.is_approved == True)
            .all()
        )

    def get_profile(self, db: Session, user_id) -> Optional[PsychologistProfile]:
        return (
            db.query(PsychologistProfile)
            .filter(PsychologistProfile.user_id == user_id)
            .first()
        )

    def update_profile(self, db: Session, user_id, data: dict) -> Optional[PsychologistProfile]:
        profile = self.get_profile(db, user_id)
        if not profile:
            return None
        for field, value in data.items():
            setattr(profile, field, value)
        db.commit()
        db.refresh(profile)
        return profile

    def register_psychologist(self, db: Session, data: dict) -> dict:
        from app.core.dependency_injection import service_locator

        user = service_locator.account_service.create_user(
            db=db,
            email=data["email"],
            full_name=data["full_name"],
            password=data["password"],
            location=data.get("location"),
            role="psychologist",
        )

        profile = PsychologistProfile(
            user_id=user.id,
            hourly_rate=data["hourly_rate"],
            bio=data.get("bio"),
            license_number=data.get("license_number"),
            years_of_experience=data.get("years_of_experience"),
            specialization=data.get("specialization"),
            about_you=data.get("about_you"),

        )
        db.add(profile)
        db.commit()
        db.refresh(user)
        db.refresh(profile)
        return {"user": user, "profile": profile}

    def create_invite(self, db: Session, admin_id, email: str, frontend_url: str) -> PsychologistInvite:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        invite = PsychologistInvite(
            email=email,
            token=token,
            invited_by=admin_id,
            expires_at=expires_at,
        )
        db.add(invite)
        db.commit()
        db.refresh(invite)
        accept_url = f"{frontend_url}/psychologist/accept-invite?token={token}"
        from app.core.dependency_injection import service_locator
        service_locator.core_service.send_slack_message(
            message=(
                f"*🎉 New Psychologist Invitation*\n\n"
                f"You have been invited to join *CerebroLearn* as a psychologist.\n\n"
                f"*👉 <{accept_url}|Click here to complete your profile>*\n\n"
                f"⏰ This link expires in *7 days*."
            ),
        )
        return invite

    def list_invites(self, db: Session) -> List[PsychologistInvite]:
        return db.query(PsychologistInvite).order_by(PsychologistInvite.created_at.desc()).all()

    def accept_invite(self, db: Session, data: dict) -> dict:
        from app.accounts.models import User
        from app.authentication.utils import hash_password

        invite = (
            db.query(PsychologistInvite)
            .filter(PsychologistInvite.token == data["token"])
            .first()
        )
        if not invite:
            raise ValueError("Invalid invite token")
        if invite.status != "pending":
            raise ValueError("Invite already used or expired")
        if datetime.now(timezone.utc) > invite.expires_at.replace(tzinfo=timezone.utc):
            invite.status = "expired"
            db.commit()
            raise ValueError("Invite token has expired")

        existing = db.query(User).filter(User.email == invite.email).first()
        if existing:
            raise ValueError("Email already registered")
        from app.core.dependency_injection import service_locator

        user = service_locator.account_service.create_user(
            db=db,
            email=invite.email,
            full_name=data["full_name"],
            password=data["password"],
            location=data.get("location"),
            role="psychologist",
            data={"is_active": True},
        )

        db.add(user)
        db.flush()

        profile = PsychologistProfile(
            user_id=user.id,
            hourly_rate=data["hourly_rate"],
            bio=data.get("bio"),
            license_number=data.get("license_number"),
            years_of_experience=data.get("years_of_experience"),
            specialization=data.get("specialization"),
            about_you=data.get("about_you"),

        )
        db.add(profile)

        invite.status = "accepted"
        db.commit()
        db.refresh(user)
        db.refresh(profile)
        return {"user": user, "profile": profile}

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
                (Booking.student_id == user_id) | (
                    Booking.psychologist_id == user_id)
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
