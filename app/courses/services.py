from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.courses.models import Course
from app.lessons.models import Section, Lesson
from app.attachment.models import Attachment
from app.accounts.models import User
from app.courses.models import CourseCollaborator
from app import settings
from itsdangerous import URLSafeTimedSerializer

signer = URLSafeTimedSerializer(settings.SECRET_KEY)


class CourseService:

    def get_course_detail(self, db: Session, course_id) -> Optional[Course]:
        return (
            db.query(Course)
            .options(
                joinedload(Course.sections).joinedload(Section.lessons),
                joinedload(Course.collaborators).joinedload(
                    CourseCollaborator.user),
            )
            .filter(Course.id == course_id)
            .first()
        )

    def create_bulk(self, db: Session, course_data: dict, sections_data: list) -> Course:
        sections_payload = course_data.pop("sections", sections_data)
        collaborators_payload = course_data.pop("collaborators", None)
        course = Course(**course_data)
        db.add(course)
        db.flush()

        for sec_data in sections_payload:
            lessons_payload = sec_data.pop("lessons", [])
            attachment_ids = sec_data.pop("attachment_ids", None) or []
            section = Section(course_id=course.id, **sec_data)
            db.add(section)
            db.flush()
            if attachment_ids:
                section.attachments = db.query(Attachment).filter(
                    Attachment.id.in_(attachment_ids)).all()
            for lesson_data in lessons_payload:
                lesson_data.pop("section_id", None)
                lesson = Lesson(section_id=section.id, **lesson_data)
                db.add(lesson)

        if collaborators_payload:
            from app.courses.models import CourseCollaborator
            from app.core.dependency_injection import service_locator
            for collab_data in collaborators_payload:
                email = collab_data["email"]
                role = collab_data["role"]
                user = db.query(User).filter(User.email == email).first()

                if not user:

                    user = User(email=email, role="instructor",
                                hashed_password="changeme", full_name="")

                    db.add(user)
                    db.flush()

                    token = signer.dumps(str(user.id))

                    set_password_url = f"{settings.FRONTEND_URL}/set-password?token={token}"

                    service_locator.core_service.send_slack_message(
                        f"Hello {email}, you've been invited to collaborate on '{course.title}'!\n\n"
                        f"We've created an account for you. Click the link below to set your password and get started:\n\n"
                        f"{set_password_url}\n\n"
                        f"This link expires in 24 hours."
                    )
                else:
                    service_locator.core_service.send_slack_message(
                        f"Hi {user.full_name or email}, great news!\n\n"
                        f"You've been added as a collaborator on '{course.title}'.\n\n"
                        f"Click here to get started: {settings.FRONTEND_URL}/dashboard"
                    )

                existing = db.query(CourseCollaborator).filter_by(
                    course_id=course.id, user_id=user.id
                ).first()
                if not existing:
                    db.add(CourseCollaborator(
                        course_id=course.id,
                        user_id=user.id,
                        role=role,
                    ))

        db.commit()
        db.refresh(course)
        return self.get_course_detail(db, course.id)

    def update_bulk(self, db: Session, course_id, course_data: dict) -> Course:
        sections_payload = course_data.pop("sections", None)
        collaborators_payload = course_data.pop("collaborators", None)

        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return None

        for key, value in course_data.items():
            if value is not None:
                setattr(course, key, value)

        if sections_payload is not None:
            existing_sections = db.query(Section).filter(
                Section.course_id == course_id).all()
            existing_section_map = {s.id: s for s in existing_sections}
            processed_section_ids = set()

            for sec_data in sections_payload:
                lessons_payload = sec_data.pop("lessons", None)
                attachment_ids = sec_data.pop("attachment_ids", None)
                sec_id = sec_data.pop("id", None)

                if sec_id and sec_id in existing_section_map:
                    section = existing_section_map[sec_id]
                    processed_section_ids.add(sec_id)
                    for key, value in sec_data.items():
                        if value is not None:
                            setattr(section, key, value)
                else:
                    section = Section(
                        course_id=course_id, **{k: v for k, v in sec_data.items() if v is not None})
                    db.add(section)
                    db.flush()
                    processed_section_ids.add(section.id)

                if attachment_ids is not None:
                    section.attachments = db.query(Attachment).filter(
                        Attachment.id.in_(attachment_ids)).all()

                if lessons_payload is not None:
                    existing_lessons = db.query(Lesson).filter(
                        Lesson.section_id == section.id).all()
                    existing_lesson_map = {l.id: l for l in existing_lessons}
                    processed_lesson_ids = set()

                    for lesson_data in lessons_payload:
                        l_id = lesson_data.pop("id", None)
                        if l_id and l_id in existing_lesson_map:
                            lesson = existing_lesson_map[l_id]
                            processed_lesson_ids.add(l_id)
                            for key, value in lesson_data.items():
                                if value is not None:
                                    setattr(lesson, key, value)
                        else:
                            lesson = Lesson(
                                section_id=section.id, **{k: v for k, v in lesson_data.items() if v is not None})
                            db.add(lesson)
                            db.flush()
                            processed_lesson_ids.add(lesson.id)

                    for lesson in [l for l in existing_lessons if l.id not in processed_lesson_ids]:
                        db.delete(lesson)

            for section in [s for s in existing_sections if s.id not in processed_section_ids]:
                db.delete(section)

        if collaborators_payload is not None:
            from app.courses.models import CourseCollaborator
            from app.core.dependency_injection import service_locator

            existing_collabs = db.query(CourseCollaborator).filter_by(
                course_id=course_id).all()
            existing_map = {c.user_id: c for c in existing_collabs}
            payload_emails = {c["email"] for c in collaborators_payload}

            for collab in existing_collabs:
                user = db.query(User).filter(User.id == collab.user_id).first()
                if user and user.email not in payload_emails:
                    db.delete(collab)
                    service_locator.core_service.send_slack_message(
                        f"Hi {user.full_name or user.email}, you've been removed as a collaborator from '{course.title}'."
                    )

            for collab_data in collaborators_payload:
                email = collab_data["email"]
                role = collab_data["role"]
                user = db.query(User).filter(User.email == email).first()

                if not user:
                    user = User(email=email, is_active=False)
                    db.add(user)
                    db.flush()
                    token = signer.dumps(str(user.id))
                    set_password_url = f"{settings.FRONTEND_URL}/set-password?token={token}"
                    service_locator.core_service.send_slack_message(
                        f"Hello {email}, you've been invited to collaborate on '{course.title}'!\n\n"
                        f"We've created an account for you. Click the link below to set your password and get started:\n\n"
                        f"{set_password_url}\n\n"
                        f"This link expires in 24 hours."
                    )
                    db.add(CourseCollaborator(
                        course_id=course_id, user_id=user.id, role=role))
                elif user.id in existing_map:
                    collab = existing_map[user.id]
                    if collab.role != role:
                        collab.role = role
                        service_locator.core_service.send_slack_message(
                            f"Hi {user.full_name or email}, your role on '{course.title}' has been updated to {role}.\n\n"
                            f"Click here to view the course: {settings.FRONTEND_URL}/dashboard"
                        )
                else:
                    db.add(CourseCollaborator(
                        course_id=course_id, user_id=user.id, role=role))
                    service_locator.core_service.send_slack_message(
                        f"Hi {user.full_name or email}, great news!\n\n"
                        f"You've been added as a collaborator on '{course.title}'.\n\n"
                        f"Click here to get started: {settings.FRONTEND_URL}/dashboard"
                    )

        db.commit()
        return self.get_course_detail(db, course_id)

    def get_creator_courses(self, db: Session, user_id) -> List[Course]:
        return (
            db.query(Course)
            .options(joinedload(Course.sections).joinedload(Section.lessons))
            .filter(Course.created_by == user_id)
            .all()
        )

    def is_owner_or_admin(self, course: Course, user) -> bool:
        return str(course.created_by) == str(user.id) or user.role == "admin"
