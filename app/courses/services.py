from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.courses.models import Course
from app.lessons.models import Section, Lesson
from app.attachment.models import Attachment


class CourseService:
    def get_with_sections(self, db: Session, course_id) -> Optional[Course]:
        return (
            db.query(Course)
            .options(
                joinedload(Course.sections).joinedload(Section.lessons)
            )
            .filter(Course.id == course_id)
            .first()
        )

    def create_bulk(self, db: Session, course_data: dict, sections_data: list) -> Course:
        sections_payload = course_data.pop("sections", sections_data)
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

        db.commit()
        db.refresh(course)
        return self.get_with_sections(db, course.id)

    def update_bulk(self, db: Session, course_id, course_data: dict) -> Course:
        sections_payload = course_data.pop("sections", None)

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

                    # Delete lessons not in payload (only if lessons were explicitly provided)
                    lessons_to_delete = [
                        l for l in existing_lessons if l.id not in processed_lesson_ids]
                    for lesson in lessons_to_delete:
                        db.delete(lesson)

            # Delete sections not in payload
            sections_to_delete = [
                s for s in existing_sections if s.id not in processed_section_ids]
            for section in sections_to_delete:
                db.delete(section)

        db.commit()
        return self.get_with_sections(db, course_id)

    def get_creator_courses(self, db: Session, user_id) -> List[Course]:
        return (
            db.query(Course)
            .options(joinedload(Course.sections).joinedload(Section.lessons))
            .filter(Course.created_by == user_id)
            .all()
        )

    def is_owner_or_admin(self, course: Course, user) -> bool:
        return str(course.created_by) == str(user.id) or user.role == "admin"
