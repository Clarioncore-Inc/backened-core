from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.courses.models import Course
from app.lessons.models import Section, Lesson


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
            section = Section(course_id=course.id, **sec_data)
            db.add(section)
            db.flush()
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

            for sec_data in sections_payload:
                lessons_payload = sec_data.pop("lessons", None)
                sec_id = sec_data.pop("id", None)

                if sec_id and sec_id in existing_section_map:
                    section = existing_section_map[sec_id]
                    for key, value in sec_data.items():
                        if value is not None:
                            setattr(section, key, value)
                else:
                    section = Section(
                        course_id=course_id, **{k: v for k, v in sec_data.items() if v is not None})
                    db.add(section)
                    db.flush()

                if lessons_payload is not None:
                    existing_lessons = db.query(Lesson).filter(
                        Lesson.section_id == section.id).all()
                    existing_lesson_map = {l.id: l for l in existing_lessons}

                    for lesson_data in lessons_payload:
                        l_id = lesson_data.pop("id", None)
                        if l_id and l_id in existing_lesson_map:
                            lesson = existing_lesson_map[l_id]
                            for key, value in lesson_data.items():
                                if value is not None:
                                    setattr(lesson, key, value)
                        else:
                            lesson = Lesson(
                                section_id=section.id, **{k: v for k, v in lesson_data.items() if v is not None})
                            db.add(lesson)

        db.commit()
        return self.get_with_sections(db, course_id)

    def get_creator_courses(self, db: Session, user_id) -> List[Course]:
        return db.query(Course).filter(Course.created_by == user_id).all()

    def is_owner_or_admin(self, course: Course, user) -> bool:
        return str(course.created_by) == str(user.id) or user.role == "admin"
