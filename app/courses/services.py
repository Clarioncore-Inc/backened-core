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

    def get_creator_courses(self, db: Session, user_id) -> List[Course]:
        return db.query(Course).filter(Course.created_by == user_id).all()

    def is_owner_or_admin(self, course: Course, user) -> bool:
        return str(course.created_by) == str(user.id) or user.role == "admin"
