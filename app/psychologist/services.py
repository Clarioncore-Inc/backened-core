import secrets
from datetime import datetime, timedelta, timezone, date
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.psychologist.models import (
    Booking, BookingStatus, MeetingConfig,
    PsychologistInvite,
    PsychologistProfile, AvailabilitySchedule
)
from app.accounts.models import User


class PsychologistService:
    def _format_booking_datetime(self, booking: Booking) -> str:
        if booking.date is None:
            return booking.time or "the scheduled time"
        return f"{booking.date.strftime('%B %d, %Y')} at {booking.time}"

    def _send_booking_rejection_slack_message(self, booking: Booking) -> None:
        from app.core.dependency_injection import service_locator

        student_name = booking.student.full_name if booking.student else "Client"
        student_email = booking.student.email if booking.student else "Unknown email"
        psychologist_name = (
            booking.psychologist.full_name if booking.psychologist else "Assigned Psychologist"
        )
        psychologist_email = (
            booking.psychologist.email if booking.psychologist else "Unknown email"
        )
        session_time = self._format_booking_datetime(booking)
        rejection_reason = booking.rejection_reason or "No reason provided."

        service_locator.core_service.send_slack_message(
            message=(
                "*Subject:* Booking Update – Consultation Request\n"
                f"*To:* {student_name} <{student_email}>\n"
                f"*From:* CerebroLearn Care Team on behalf of {psychologist_name} <{psychologist_email}>\n\n"
                f"Dear {student_name},\n\n"
                "Thank you for booking a consultation through CerebroLearn. "
                f"After reviewing your request for {session_time}, {psychologist_name} is unable to accept the booking at this time.\n\n"
                "Reason provided by the psychologist:\n"
                f"{rejection_reason}\n\n"
                "Next steps:\n"
                "• Review the update on your booking page.\n"
                "• Book another available time slot that works for you.\n"
                "• Contact support if you need assistance finding a new session.\n\n"
                "Warm regards,\n"
                "CerebroLearn Care Team"
            )
        )

    def _send_booking_confirmation_slack_message(self, booking: Booking, db: Session) -> None:
        from app.core.dependency_injection import service_locator

        student_name = booking.student.full_name if booking.student else "Client"
        student_email = booking.student.email if booking.student else "Unknown email"
        psychologist_name = (
            booking.psychologist.full_name if booking.psychologist else "Assigned Psychologist"
        )
        session_time = self._format_booking_datetime(booking)

        # Fetch the global meeting config (may not exist yet)
        meeting_config = db.query(MeetingConfig).first()
        if meeting_config:
            meeting_block = (
                f"\n*Meeting Details:*\n"
                f"• Platform: {meeting_config.name}\n"
                f"• Link: {meeting_config.link}\n"
                + (f"• Password: {meeting_config.password}\n" if meeting_config.password else "")
            )
        else:
            meeting_block = "\nThe meeting link will be shared with you shortly.\n"

        service_locator.core_service.send_slack_message(
            message=(
                "*Subject:* Booking Confirmed – Consultation Scheduled\n"
                f"*To:* {student_name} <{student_email}>\n"
                f"*From:* CerebroLearn Care Team on behalf of {psychologist_name}\n\n"
                f"Dear {student_name},\n\n"
                f"Great news! Your consultation with {psychologist_name} has been *confirmed* for {session_time}."
                f"{meeting_block}\n"
                "Please join the meeting a few minutes early. If you have any questions, "
                "feel free to reach out to our support team.\n\n"
                "Warm regards,\n"
                "CerebroLearn Care Team"
            )
        )

    def list_approved(self, db: Session) -> List[PsychologistProfile]:
        return (
            db.query(PsychologistProfile)
            .filter(PsychologistProfile.is_approved == True)
            .all()
        )

    def list_all(self, db: Session) -> List[PsychologistProfile]:
        return db.query(PsychologistProfile).all()

    def get_profile(self, db: Session, user_id) -> Optional[PsychologistProfile]:
        return (
            db.query(PsychologistProfile)
            .filter(PsychologistProfile.user_id == user_id)
            .first()
        )

    def get_profile_by_id(self, db: Session, profile_id) -> Optional[PsychologistProfile]:
        return (
            db.query(PsychologistProfile)
            .filter(PsychologistProfile.id == profile_id)
            .first()
        )

    def _apply_profile_updates(self, db: Session, profile: PsychologistProfile, data: dict) -> PsychologistProfile:
        from app.core.dependency_injection import service_locator

        updates = dict(data)
        user_updates = dict(updates.pop("user", {}) or {})

        legacy_location = updates.pop("location", None)
        if legacy_location is not None and "location" not in user_updates:
            user_updates["location"] = legacy_location

        if user_updates and profile.user:
            service_locator.account_service.update_profile(
                db=db,
                user=profile.user,
                updates=user_updates,
            )

        for field, value in updates.items():
            setattr(profile, field, value)

        db.commit()
        db.refresh(profile)
        return profile

    def update_profile(self, db: Session, user_id, data: dict) -> Optional[PsychologistProfile]:
        profile = self.get_profile(db, user_id)
        if not profile:
            return None
        return self._apply_profile_updates(db=db, profile=profile, data=data)

    def update_profile_by_id(self, db: Session, profile_id, data: dict) -> Optional[PsychologistProfile]:
        profile = self.get_profile_by_id(db, profile_id)
        if not profile:
            return None
        return self._apply_profile_updates(db=db, profile=profile, data=data)

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
            bio=data.get("bio"),
            license_number=data.get("license_number"),
            years_of_experience=data.get("years_of_experience"),
            specialization=data.get("specialization"),
            about_you=data.get("about_you"),
            default_session_duration=data.get("default_session_duration"),
            default_booking_type=data.get("default_booking_type"),
            allow_emergency_bookings=data.get(
                "allow_emergency_bookings", False),
            is_profile_public=data.get("is_profile_public", True),
            accepting_new_clients=data.get("accepting_new_clients", True),
            visible_profile_fields=data.get("visible_profile_fields"),

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
        accept_url = f"{frontend_url}/?join=psychologist&token={token}"
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
            default_session_duration=data.get("default_session_duration"),
            default_booking_type=data.get("default_booking_type"),
            allow_emergency_bookings=data.get(
                "allow_emergency_bookings", False),
            is_profile_public=data.get("is_profile_public", True),
            accepting_new_clients=data.get("accepting_new_clients", True),
            visible_profile_fields=data.get("visible_profile_fields"),

        )
        db.add(profile)

        invite.status = "accepted"
        db.commit()
        db.refresh(user)
        db.refresh(profile)
        return {"user": user, "profile": profile}

    def create_booking(self, db: Session, student_id, data: dict) -> Booking:
        data["student_id"] = student_id
        data["status"] = data.get("status") or BookingStatus.PENDING.value
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

    def transition_booking_status(self, db: Session, booking_id, psychologist_id, data: dict) -> Optional[Booking]:
        booking = (
            db.query(Booking)
            .filter(
                Booking.id == booking_id,
                Booking.psychologist_id == psychologist_id,
            )
            .first()
        )
        if not booking:
            return None

        next_status = data.get("status")
        if isinstance(next_status, BookingStatus):
            next_status = next_status.value

        allowed_statuses = {
            BookingStatus.CONFIRMED.value,
            BookingStatus.CANCELLED.value,
            BookingStatus.COMPLETED.value,
        }
        if next_status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Booking status can only be changed to confirmed, cancelled, or completed",
            )

        previous_status = booking.status
        rejection_reason = data.get("rejection_reason")

        if next_status == BookingStatus.CANCELLED.value:
            if not rejection_reason:
                raise HTTPException(
                    status_code=400,
                    detail="Rejection reason is required when rejecting a booking",
                )
            booking.rejection_reason = rejection_reason
        else:
            booking.rejection_reason = None

        if next_status == BookingStatus.COMPLETED.value:
            session_summary = (booking.session_notes or {}
                               ).get("session_summary")
            if not session_summary:
                raise HTTPException(
                    status_code=400,
                    detail="Session notes are required before marking the booking as done",
                )

        booking.status = next_status
        db.commit()
        db.refresh(booking)

        if next_status == BookingStatus.CANCELLED.value and previous_status != BookingStatus.CANCELLED.value:
            self._send_booking_rejection_slack_message(booking)

        if next_status == BookingStatus.CONFIRMED.value and previous_status != BookingStatus.CONFIRMED.value:
            self._send_booking_confirmation_slack_message(booking, db)

        return booking

    def upsert_booking_notes(self, db: Session, booking_id, psychologist_id, data: dict) -> Optional[Booking]:
        booking = (
            db.query(Booking)
            .filter(
                Booking.id == booking_id,
                Booking.psychologist_id == psychologist_id,
            )
            .first()
        )
        if not booking:
            return None

        current_notes = dict(booking.session_notes or {})
        current_notes.update(data)

        session_summary = current_notes.get("session_summary")
        is_cancelled = booking.status == BookingStatus.CANCELLED.value
        if not is_cancelled and not session_summary:
            raise HTTPException(
                status_code=400,
                detail="Session summary is required unless the client cancelled",
            )

        booking.session_notes = current_notes or None
        booking.session_notes_updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(booking)
        return booking

    def get_booking_notes(self, db: Session, booking_id, psychologist_id) -> Optional[Booking]:
        return (
            db.query(Booking)
            .filter(
                Booking.id == booking_id,
                Booking.psychologist_id == psychologist_id,
            )
            .first()
        )

    def resolve_user_id(self, db: Session, identifier: UUID) -> UUID:
        profile = db.query(PsychologistProfile).filter(
            PsychologistProfile.id == identifier
        ).first()
        if profile:
            return profile.user_id

        user = db.query(User).filter(User.id == identifier).first()
        if user:
            return user.id

        raise HTTPException(
            status_code=404, detail="User or psychologist not found")

    def get_available_psychologist_for_booking(
        self,
        db: Session,
        booking_date: date,
        booking_time: str,  # e.g. "14:00"
        booking_type: str = "standard",
    ) -> Optional[PsychologistProfile]:
        """
        Returns the best psychologist to assign a booking to.

        Rules:
        1. Must be approved and accepting new clients
        2. Must allow emergency bookings (if booking_type is 'emergency')
        3. Must be available on the booking day and the time must fall within their schedule window
        4. Prefer psychologists with zero active bookings (completely free)
        5. If all have active bookings, pick the least loaded
        6. A psychologist must NOT be occupied while others are free
        """
        from core.dependency_injection import service_locator

        # Step 1: Filter base candidates via filter_data
        filters = {
            "is_approved": True,
            "accepting_new_clients": True,
        }
        if booking_type == "emergency":
            filters["allow_emergency_bookings"] = True

        candidates: List[PsychologistProfile] = service_locator.general_service.filter_data(
            db, PsychologistProfile, filters
        )

        if not candidates:
            return None

        # Step 2: Filter by availability schedule
        # booking_date.strftime("%A").lower() → e.g. "monday", "tuesday"
        day_name = booking_date.strftime("%A").lower()

        try:
            booking_time_obj = datetime.strptime(booking_time, "%H:%M").time()
        except (ValueError, TypeError):
            booking_time_obj = None

        available_candidates: List[PsychologistProfile] = []

        for psych in candidates:
            schedule_row = (
                db.query(AvailabilitySchedule)
                .filter(AvailabilitySchedule.psychologist_id == psych.user_id)
                .first()
            )

            # No schedule row → skip (treat as unavailable)
            if not schedule_row or not schedule_row.schedule:
                continue

            day_schedule = schedule_row.schedule.get(day_name)

            # Day not in schedule or not enabled → skip
            if not day_schedule or not day_schedule.get("enabled", False):
                continue

            # If a booking time was provided, check it falls within the window
            if booking_time_obj:
                try:
                    window_start = datetime.strptime(
                        day_schedule["start"], "%H:%M").time()
                    window_end = datetime.strptime(
                        day_schedule["end"], "%H:%M").time()
                except (KeyError, ValueError):
                    continue

                if not (window_start <= booking_time_obj <= window_end):
                    continue

            available_candidates.append(psych)

        if not available_candidates:
            return None

        # Step 3: Score each available psychologist by active booking load
        active_statuses = [
            BookingStatus.PENDING.value,
            BookingStatus.CONFIRMED.value,
            BookingStatus.EMERGENCY.value,
        ]

        scored: List[tuple[PsychologistProfile, int]] = []

        for psych in available_candidates:
            active_count = (
                db.query(Booking)
                .filter(
                    Booking.psychologist_id == psych.user_id,
                    Booking.status.in_(active_statuses),
                )
                .count()
            )
            scored.append((psych, active_count))

        # Step 4: Enforce fairness — free psychologist always wins
        free = [psych for psych, count in scored if count == 0]
        if free:
            return free[0]

        # Step 5: All are occupied — return least loaded
        scored.sort(key=lambda x: x[1])
        return scored[0][0]

    def check_psychologist_availability(
        self,
        db: Session,
        psychologist_id: UUID,
        booking_date: date,
        booking_time: str,  # e.g. "14:00"
    ) -> dict:
        """
        Checks if a specific psychologist is available at the given date and time.
        Returns a dict with available: bool and a reason if not.
        """

        # Step 1: Get the profile
        profile = self.get_profile(db, user_id=psychologist_id)
        if not profile:
            return {"available": False, "reason": "Psychologist not found."}

        if not profile.is_approved:
            return {"available": False, "reason": "Psychologist is not approved."}

        if not profile.accepting_new_clients:
            return {"available": False, "reason": "Psychologist is not accepting new clients."}

        # Step 2: Check availability schedule
        day_name = booking_date.strftime("%A").lower()

        schedule_row = (
            db.query(AvailabilitySchedule)
            .filter(AvailabilitySchedule.psychologist_id == psychologist_id)
            .first()
        )

        if not schedule_row or not schedule_row.schedule:
            return {"available": False, "reason": "Psychologist has no availability schedule set."}

        day_schedule = schedule_row.schedule.get(day_name)

        if not day_schedule or not day_schedule.get("enabled", False):
            return {
                "available": False,
                "reason": f"Psychologist is not available on {day_name.capitalize()}s.",
            }

        try:
            booking_time_obj = datetime.strptime(booking_time, "%H:%M").time()
            window_start = datetime.strptime(
                day_schedule["start"], "%H:%M").time()
            window_end = datetime.strptime(day_schedule["end"], "%H:%M").time()
        except (ValueError, KeyError):
            return {"available": False, "reason": "Invalid time format."}

        if not (window_start <= booking_time_obj <= window_end):
            return {
                "available": False,
                "reason": (
                    f"Psychologist is only available between "
                    f"{day_schedule['start']} and {day_schedule['end']} "
                    f"on {day_name.capitalize()}s."
                ),
            }

        # Step 3: Check for a conflicting booking at the exact same time
        conflict = (
            db.query(Booking)
            .filter(
                Booking.psychologist_id == psychologist_id,
                Booking.date == booking_date,
                Booking.time == booking_time,
                Booking.status.in_([
                    BookingStatus.PENDING.value,
                    BookingStatus.CONFIRMED.value,
                    BookingStatus.EMERGENCY.value,
                ]),
            )
            .first()
        )

        if conflict:
            return {
                "available": False,
                "reason": f"Psychologist already has a booking at {booking_time} on that day.",
            }

        return {"available": True, "reason": None}
