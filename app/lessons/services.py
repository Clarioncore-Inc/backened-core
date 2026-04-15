from typing import List, Optional
from sqlalchemy.orm import Session, joinedload, selectinload
from app.lessons.models import (
    CalloutLesson,
    CodeLesson,
    HeadingLesson,
    HintLesson,
    ImageLesson,
    InteractiveLesson,
    InteractiveStep,
    Lesson,
    LessonBookmark,
    LessonComment,
    LessonLike,
    ProblemLesson,
    QuizLesson,
    QuizQuestion,
    Section,
    TextLesson,
    TextLessonAttachment,
    VideoLesson,
)


class LessonService:
    def get_lesson_detail(self, db: Session, lesson_id) -> Optional[Lesson]:
        return (
            db.query(Lesson)
            .options(
                selectinload(Lesson.video_content).selectinload(VideoLesson.video),
                selectinload(Lesson.video_content).selectinload(VideoLesson.thumbnail),
                selectinload(Lesson.video_content).selectinload(VideoLesson.subtitles),
                selectinload(Lesson.text_content)
                .selectinload(TextLesson.attachments)
                .selectinload(TextLessonAttachment.attachment),
                selectinload(Lesson.quiz_content)
                .selectinload(QuizLesson.questions)
                .selectinload(QuizQuestion.options),
                selectinload(Lesson.quiz_content)
                .selectinload(QuizLesson.questions)
                .selectinload(QuizQuestion.image),
                selectinload(Lesson.interactive_content)
                .selectinload(InteractiveLesson.steps)
                .selectinload(InteractiveStep.image),
                selectinload(Lesson.problem_content).selectinload(ProblemLesson.image),
                selectinload(Lesson.problem_content).selectinload(ProblemLesson.test_cases),
                selectinload(Lesson.heading_content),
                selectinload(Lesson.image_content).selectinload(ImageLesson.image),
                selectinload(Lesson.code_content),
                selectinload(Lesson.hint_content),
                selectinload(Lesson.callout_content),
            )
            .filter(Lesson.id == lesson_id)
            .first()
        )

    def get_section_with_lessons(self, db: Session, section_id) -> Optional[Section]:
        return (
            db.query(Section)
            .options(joinedload(Section.lessons))
            .filter(Section.id == section_id)
            .first()
        )

    def get_comments(self, db: Session, lesson_id) -> List[LessonComment]:
        return (
            db.query(LessonComment)
            .filter(LessonComment.lesson_id == lesson_id)
            .order_by(LessonComment.created_at)
            .all()
        )

    def get_bookmarks(self, db: Session, user_id) -> List[LessonBookmark]:
        return db.query(LessonBookmark).filter(LessonBookmark.user_id == user_id).all()

    def add_like(self, db: Session, user_id, lesson_id) -> Lesson:
        existing = (
            db.query(LessonLike)
            .filter(LessonLike.user_id == user_id, LessonLike.lesson_id == lesson_id)
            .first()
        )
        if not existing:
            like = LessonLike(user_id=user_id, lesson_id=lesson_id)
            db.add(like)
            lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
            if lesson:
                lesson.like_count = (lesson.like_count or 0) + 1
            db.commit()
            db.refresh(lesson)
            return lesson
        return db.query(Lesson).filter(Lesson.id == lesson_id).first()

    def remove_like(self, db: Session, user_id, lesson_id) -> Optional[Lesson]:
        like = (
            db.query(LessonLike)
            .filter(LessonLike.user_id == user_id, LessonLike.lesson_id == lesson_id)
            .first()
        )
        if like:
            db.delete(like)
            lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
            if lesson and lesson.like_count > 0:
                lesson.like_count -= 1
            db.commit()
            db.refresh(lesson)
            return lesson
        return None

    def add_bookmark(self, db: Session, user_id, lesson_id) -> LessonBookmark:
        existing = (
            db.query(LessonBookmark)
            .filter(LessonBookmark.user_id == user_id, LessonBookmark.lesson_id == lesson_id)
            .first()
        )
        if not existing:
            bookmark = LessonBookmark(user_id=user_id, lesson_id=lesson_id)
            db.add(bookmark)
            db.commit()
            db.refresh(bookmark)
            return bookmark
        return existing

    def add_comment(self, db: Session, user_id, data: dict) -> LessonComment:
        comment = LessonComment(user_id=user_id, **data)
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment
