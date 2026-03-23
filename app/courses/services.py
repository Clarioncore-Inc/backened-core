from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.courses.models import Course
from app.lessons.models import Lesson


class CourseService:
    def get_with_lessons(
        self, db: Session, course_id
    ) -> Optional[Tuple[Course, List[Lesson]]]:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return None
        lessons = (
            db.query(Lesson)
            .filter(Lesson.course_id == course_id)
            .order_by(Lesson.position)
            .all()
        )
        return course, lessons

    def get_public_courses(self, db: Session) -> List[Course]:
        return (
            db.query(Course)
            .filter(Course.is_public == True, Course.status == "published")
            .all()
        )

    def get_creator_courses(self, db: Session, user_id) -> List[Course]:
        return db.query(Course).filter(Course.created_by == user_id).all()

    def is_owner_or_admin(self, course: Course, user) -> bool:
        return str(course.created_by) == str(user.id) or user.role == "admin"

