import secrets
import logging
from calendar import monthrange
from datetime import datetime, timedelta, timezone, date
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.general.models import AppSettings
from app.psychologist.models import (
    Booking, BookingStatus, MeetingConfig,
    PsychologistInvite,
    PsychologistProfile, AvailabilitySchedule
)
from app.accounts.models import User
logger = logging.getLogger(__name__)

class PsychologistService:
    _pending_booking_reminder_cache: dict[str, str] = {}

    def _format_booking_datetime(self, booking: Booking) -> str:
        if booking.date is None:
            return booking.time or "the scheduled time"
        return f"{booking.date.strftime('%B %d, %Y')} at {booking.time}"

    def _parse_booking_datetime(self, booking: Booking) -> Optional[datetime]:
        if booking.date is None or not booking.time:
            return None

        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                parsed_time = datetime.strptime(booking.time, fmt).time()
                return datetime.combine(booking.date, parsed_time)
            except ValueError:
                continue

        return None

    def _send_pending_booking_admin_reminder(
        self,
        overdue_bookings: List[Booking],
        admin_users: List[User],
        reminder_minutes: int,
    ) -> None:
        from app.core.dependency_injection import service_locator

        admin_targets = ", ".join(
            f"{admin.full_name} <{admin.email}>" if admin.email else admin.full_name
            for admin in admin_users
        ) or "Admin team"

        lines: List[str] = []
        for booking in overdue_bookings[:10]:
            student_name = booking.student.full_name if booking.student else "Client"
            student_email = booking.student.email if booking.student else "Unknown email"
            psychologist_name = (
                booking.psychologist.full_name if booking.psychologist else "Assigned Psychologist"
            )
            lines.append(
                f"• {student_name} <{student_email}> — {self._format_booking_datetime(booking)} — Psychologist: {psychologist_name}"
            )

        if len(overdue_bookings) > 10:
            lines.append(f"• ...and {len(overdue_bookings) - 10} more overdue booking(s)")

        service_locator.core_service.send_slack_message(
            message=(
                "*⚠️ Pending Booking Reminder*\n\n"
                f"*To:* {admin_targets}\n\n"
                f"The following booking request(s) are still *pending acknowledgement* more than *{reminder_minutes} minute(s)* after the scheduled booking time:\n"
                f"{'\n'.join(lines)}\n\n"
                "Please review these bookings in the psychologist dashboard."
            )
        )

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
                "Please note that this booking is subject to change.\n"
                "Please join the meeting a few minutes early. If you have any questions, "
                "feel free to reach out to our support team at cerebrolearn@example.com.\n\n"
                "Warm regards,\n"
                "CerebroLearn Care Team"
            )
        )

    def list_approved(self, db: Session) -> List[PsychologistProfile]:
        return (
            db.query(PsychologistProfile)
            .filter(PsychologistProfile.status == "approved")
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

    def _send_booking_created_psychologist_slack_message(self, booking: Booking) -> None:
        from app.core.dependency_injection import service_locator

        psychologist_name = (
            booking.psychologist.full_name if booking.psychologist else "Psychologist"
        )
        psychologist_email = (
            booking.psychologist.email if booking.psychologist else ""
        )
        student_name = booking.student.full_name if booking.student else "A client"
        session_time = self._format_booking_datetime(booking)
        booking_type = (booking.booking_type or "standard").capitalize()
        notes = booking.notes or "None provided."

        service_locator.core_service.send_slack_message(
            message=(
                f"*🔔 New Booking Request – Action Required*\n\n"
                f"*To:* {psychologist_name} <{psychologist_email}>\n\n"
                f"Dear {psychologist_name},\n\n"
                f"You have received a new consultation request from *{student_name}*.\n\n"
                f"*Session Details:*\n"
                f"• Date & Time: {session_time}\n"
                f"Please log in to your CerebroLearn dashboard to *acknowledge* this booking.\n\n"
                f"Warm regards,\n"
                f"CerebroLearn Care Team"
            )
        )

    def _send_booking_created_student_slack_message(self, booking: Booking, db: Session) -> None:
        from app.core.dependency_injection import service_locator

        student_name = booking.student.full_name if booking.student else "there"
        student_email = booking.student.email if booking.student else ""
        session_time = self._format_booking_datetime(booking)
        support_email = "support@example.com"
        try:
            app_settings = service_locator.general_service.get_app_settings(db=db)
            support_email = app_settings.email or support_email
        except Exception:
            logger.exception("Failed to load app settings for booking confirmation Slack message")

        service_locator.core_service.send_slack_message(
            message=(
                f"*✅ Booking Received – Pending Confirmation*\n\n"
                f"*To:* {student_name} <{student_email}>\n\n"
                f"Dear {student_name},\n\n"
                f"Your consultation booking for *{session_time}* has been successfully received.\n\n"
                f"Please note that this booking is subject to change.\n\n"
                f"You will be notified as soon as your session is confirmed. "
                f"In the meantime, you can view your booking status on your dashboard under *My Sessions*.\n\n"
                f"If you have any questions, feel free to reach out to our support team at {support_email}.\n\n"
                f"Warm regards,\n"
                f"CerebroLearn Care Team"
            )
        )

    def create_booking(self, db: Session, student_id, data: dict) -> Booking:
        psychologist = self.get_available_psychologist_for_booking(
            db=db,
            booking_date=data["date"],
            booking_time=data.get("time"),
            booking_type=data.get("booking_type", "standard"),
        )

        if not psychologist:
            raise HTTPException(
                status_code=400,
                detail="No psychologist is available at the selected date and time.",
            )

        data["student_id"] = student_id
        data["psychologist_id"] = psychologist.user_id
        data["status"] = data.get("status") or BookingStatus.PENDING.value

        booking = Booking(**data)
        db.add(booking)
        db.commit()
        db.refresh(booking)

        try:
            self._send_booking_created_psychologist_slack_message(booking)
        except Exception:
            logger.error(f"Failed to send booking confirmation Slack message for booking ID {booking.id}")

        try:
            self._send_booking_created_student_slack_message(booking, db)
        except Exception as e:
            logger.error(f"Failed to send booking confirmation Slack message for booking ID {booking.id}: {e}")

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
            session_notes = booking.session_notes or {}
            session_summary = session_notes.get("session_summary")
            cognitive_profile = session_notes.get("cognitive_profile")
            has_cognitive_profile = isinstance(cognitive_profile, dict) and any(
                value not in (None, "") for value in cognitive_profile.values()
            )

            if not session_summary and not has_cognitive_profile:
                raise HTTPException(
                    status_code=400,
                    detail="Session results are required before marking the booking as done",
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
        next_notes = {
            key: value
            for key, value in {
                "meeting_platform": current_notes.get("meeting_platform"),
                "meeting_link": current_notes.get("meeting_link"),
            }.items()
            if value not in (None, "")
        }
        next_notes.update(data)

        cognitive_profile = next_notes.get("cognitive_profile")
        is_cancelled = booking.status == BookingStatus.CANCELLED.value
        if not is_cancelled and not cognitive_profile:
            raise HTTPException(
                status_code=400,
                detail="Cognitive profile scores are required unless the client cancelled",
            )

        booking.session_notes = next_notes or None
        booking.session_notes_updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(booking)
        return booking

    def check_pending_bookings_reminder(self, db: Session) -> int:
        bind = db.get_bind()
        if bind is None or not inspect(bind).has_table(AppSettings.__tablename__):
            return 0

        settings = db.query(AppSettings).order_by(AppSettings.created_at.asc()).first()
        reminder_minutes = int(
            getattr(settings, "psychologist_booking_reminder_in_minutes", 30) or 30
        )
        if reminder_minutes <= 0:
            self._pending_booking_reminder_cache = {}
            return 0

        now = datetime.now()
        pending_bookings = (
            db.query(Booking)
            .filter(Booking.status == BookingStatus.PENDING.value)
            .all()
        )

        current_cache_keys: set[str] = set()
        overdue_to_notify: List[tuple[str, Booking]] = []

        for booking in pending_bookings:
            booking_datetime = self._parse_booking_datetime(booking)
            if booking_datetime is None:
                continue

            if booking_datetime + timedelta(minutes=reminder_minutes) > now:
                continue

            cache_key = (
                f"{booking.id}:{booking.updated_at.isoformat() if booking.updated_at else ''}"
            )
            current_cache_keys.add(cache_key)

            if cache_key in self._pending_booking_reminder_cache:
                continue

            overdue_to_notify.append((cache_key, booking))

        self._pending_booking_reminder_cache = {
            key: sent_at
            for key, sent_at in self._pending_booking_reminder_cache.items()
            if key in current_cache_keys
        }

        if not overdue_to_notify:
            return 0

        admin_users = (
            db.query(User)
            .filter(User.role.in_(["admin", "org_admin"]))
            .all()
        )
        if not admin_users:
            return 0

        overdue_bookings = [booking for _, booking in overdue_to_notify]
        self._send_pending_booking_admin_reminder(
            overdue_bookings=overdue_bookings,
            admin_users=admin_users,
            reminder_minutes=reminder_minutes,
        )

        sent_at = datetime.utcnow().isoformat()
        for cache_key, _ in overdue_to_notify:
            self._pending_booking_reminder_cache[cache_key] = sent_at

        return len(overdue_bookings)

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
        2. Must be available on the booking day and the time must fall within their schedule window
        3. Prefer psychologists with zero active bookings (completely free)
        4. If all have active bookings, pick the least loaded
        5. A psychologist must NOT be occupied while others are free
        """
        from app.core.dependency_injection import service_locator

        # Step 1: Filter base candidates via filter_data
        filters = {
            "status": "approved",
        }

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

    def get_available_slots(
        self,
        db: Session,
        booking_date: date,
        booking_type: str = "standard",
    ) -> List[str]:
        from app.core.dependency_injection import service_locator

        filters = {"status": "approved"}

        candidates: List[PsychologistProfile] = service_locator.general_service.filter_data(
            db, PsychologistProfile, filters
        )

        if not candidates:
            return []

        day_name = booking_date.strftime("%A").lower()

        active_statuses = [
            BookingStatus.PENDING.value,
            BookingStatus.CONFIRMED.value,
            BookingStatus.EMERGENCY.value,
        ]

        # Fetch ALL booked times for this date in one query
        all_booked = (
            db.query(Booking.psychologist_id, Booking.time)
            .filter(
                Booking.date == booking_date,
                Booking.status.in_(active_statuses),
            )
            .all()
        )
        # {psychologist_id: {time, time, ...}}
        booked_map: dict = {}
        for psych_id, time in all_booked:
            booked_map.setdefault(psych_id, set()).add(time)

        # Fetch ALL schedules in one query
        psych_ids = [p.user_id for p in candidates]
        schedule_rows = (
            db.query(AvailabilitySchedule)
            .filter(AvailabilitySchedule.psychologist_id.in_(psych_ids))
            .all()
        )
        schedule_map = {row.psychologist_id: row for row in schedule_rows}

        # Build available slots
        available_slots: set[str] = set()

        for psych in candidates:
            schedule_row = schedule_map.get(psych.user_id)

            if not schedule_row or not schedule_row.schedule:
                continue

            day_schedule = schedule_row.schedule.get(day_name)

            if not day_schedule or not day_schedule.get("enabled", False):
                continue

            try:
                window_start = datetime.strptime(
                    day_schedule["start"], "%H:%M")
                window_end = datetime.strptime(day_schedule["end"], "%H:%M")
            except (KeyError, ValueError):
                continue

            booked_times = booked_map.get(psych.user_id, set())
            duration = psych.default_session_duration or 60
            current = window_start

            while current + timedelta(minutes=duration) <= window_end:
                slot = current.strftime("%H:%M")
                if slot not in booked_times:
                    available_slots.add(slot)
                current += timedelta(minutes=duration)

        return sorted(available_slots)

    def get_available_dates(
        self,
        db: Session,
        year: int,
        month: int,
        booking_type: str = "standard",
    ) -> List[str]:
        from app.core.dependency_injection import service_locator

        filters = {"status": "approved"}

        candidates: List[PsychologistProfile] = service_locator.general_service.filter_data(
            db, PsychologistProfile, filters
        )

        if not candidates:
            return []

        psych_ids = [p.user_id for p in candidates]
        schedule_rows = (
            db.query(AvailabilitySchedule)
            .filter(AvailabilitySchedule.psychologist_id.in_(psych_ids))
            .all()
        )

        enabled_weekdays: set[str] = set()
        for schedule_row in schedule_rows:
            schedule = schedule_row.schedule or {}
            for weekday_name, day_schedule in schedule.items():
                if not isinstance(day_schedule, dict):
                    continue

                if not day_schedule.get("enabled", False):
                    continue

                try:
                    window_start = datetime.strptime(day_schedule["start"], "%H:%M")
                    window_end = datetime.strptime(day_schedule["end"], "%H:%M")
                except (KeyError, TypeError, ValueError):
                    continue

                if window_start >= window_end:
                    continue

                enabled_weekdays.add(str(weekday_name).lower())

        if not enabled_weekdays:
            return []

        _, days_in_month = monthrange(year, month)
        today_value = date.today()
        available_dates: List[str] = []

        for day in range(1, days_in_month + 1):
            booking_date = date(year, month, day)
            if booking_date < today_value:
                continue

            weekday_name = booking_date.strftime("%A").lower()
            if weekday_name not in enabled_weekdays:
                continue

            slots = self.get_available_slots(
                db=db,
                booking_date=booking_date,
                booking_type=booking_type,
            )
            if slots:
                available_dates.append(booking_date.isoformat())

        return available_dates
