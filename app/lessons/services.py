from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.lessons.models import (
    CalloutLesson,
    CodeLesson,
    HeadingLesson,
    HintLesson,
    ImageLesson,
    InteractiveLesson,
    # InteractiveStep,
    Lesson,
    LessonBookmark,
    LessonComment,
    LessonLike,
    ProblemLesson,
    QuizLesson,
    # QuizQuestion,
    Section,
    TextLesson,
    # TextLessonAttachment,
    VideoLesson,
    LessonContentMixin

)
from app.lessons.schemas.lesson_contents import ChildContentResponse


class LessonService:
    def get_lesson_detail(self, db: Session, lesson_id) -> Optional[Lesson]:
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            return None

        lesson.video_content = db.query(VideoLesson).filter_by(
            lesson_id=lesson_id, parent_id=None).order_by(VideoLesson.position).all()
        lesson.text_content = db.query(TextLesson).filter_by(
            lesson_id=lesson_id, parent_id=None).order_by(TextLesson.position).all()
        lesson.quiz_content = db.query(QuizLesson).filter_by(
            lesson_id=lesson_id, parent_id=None).order_by(QuizLesson.position).all()
        lesson.interactive_content = db.query(InteractiveLesson).filter_by(
            lesson_id=lesson_id, parent_id=None).order_by(InteractiveLesson.position).all()
        lesson.problem_content = db.query(ProblemLesson).filter_by(
            lesson_id=lesson_id, parent_id=None).order_by(ProblemLesson.position).all()
        lesson.heading_content = db.query(HeadingLesson).filter_by(
            lesson_id=lesson_id, parent_id=None).order_by(HeadingLesson.position).all()
        lesson.image_content = db.query(ImageLesson).filter_by(
            lesson_id=lesson_id, parent_id=None).order_by(ImageLesson.position).all()
        lesson.code_content = db.query(CodeLesson).filter_by(
            lesson_id=lesson_id, parent_id=None).order_by(CodeLesson.position).all()
        lesson.hint_content = db.query(HintLesson).filter_by(
            lesson_id=lesson_id, parent_id=None).order_by(HintLesson.position).all()
        lesson.callout_content = db.query(CalloutLesson).filter_by(
            lesson_id=lesson_id, parent_id=None).order_by(CalloutLesson.position).all()

        for block_list, parent_type in [
            (lesson.video_content, LessonContentMixin.ParentType.VIDEO_LESSON),
            (lesson.text_content, LessonContentMixin.ParentType.TEXT_LESSON),
            (lesson.quiz_content, LessonContentMixin.ParentType.QUIZ_LESSON),
            (lesson.interactive_content,
             LessonContentMixin.ParentType.INTERACTIVE_LESSON),
            (lesson.problem_content, LessonContentMixin.ParentType.PROBLEM_LESSON),
            (lesson.heading_content, LessonContentMixin.ParentType.HEADING_LESSON),
            (lesson.image_content, LessonContentMixin.ParentType.IMAGE_LESSON),
            (lesson.code_content, LessonContentMixin.ParentType.CODE_LESSON),
            (lesson.hint_content, LessonContentMixin.ParentType.HINT_LESSON),
            (lesson.callout_content, LessonContentMixin.ParentType.CALLOUT_LESSON),
        ]:
            for block in block_list:
                block.children = self.get_children(
                    db, parent_id=block.id, parent_type=parent_type)

        return lesson

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

    def determine_parent_type(self, db: Session, parent_id: UUID) -> str:
        checks = [
            (VideoLesson, LessonContentMixin.ParentType.VIDEO_LESSON),
            (TextLesson, LessonContentMixin.ParentType.TEXT_LESSON),
            (QuizLesson, LessonContentMixin.ParentType.QUIZ_LESSON),
            (InteractiveLesson, LessonContentMixin.ParentType.INTERACTIVE_LESSON),
            (ProblemLesson, LessonContentMixin.ParentType.PROBLEM_LESSON),
            (HeadingLesson, LessonContentMixin.ParentType.HEADING_LESSON),
            (ImageLesson, LessonContentMixin.ParentType.IMAGE_LESSON),
            (CodeLesson, LessonContentMixin.ParentType.CODE_LESSON),
            (HintLesson, LessonContentMixin.ParentType.HINT_LESSON),
            (CalloutLesson, LessonContentMixin.ParentType.CALLOUT_LESSON),
        ]
        for model, type_str in checks:
            if db.query(model).filter_by(id=parent_id).first():
                return type_str
        raise HTTPException(
            status_code=400, detail="Invalid parent_id — no matching content block found")

    def get_children(self, db: Session, parent_id: UUID, parent_type: str) -> ChildContentResponse:
        return ChildContentResponse(
            video_content=db.query(VideoLesson).filter_by(
                parent_id=parent_id, parent_type=parent_type).order_by(VideoLesson.position).all(),
            text_content=db.query(TextLesson).filter_by(
                parent_id=parent_id, parent_type=parent_type).order_by(TextLesson.position).all(),
            quiz_content=db.query(QuizLesson).filter_by(
                parent_id=parent_id, parent_type=parent_type).order_by(QuizLesson.position).all(),
            interactive_content=db.query(InteractiveLesson).filter_by(
                parent_id=parent_id, parent_type=parent_type).order_by(InteractiveLesson.position).all(),
            problem_content=db.query(ProblemLesson).filter_by(
                parent_id=parent_id, parent_type=parent_type).order_by(ProblemLesson.position).all(),
            heading_content=db.query(HeadingLesson).filter_by(
                parent_id=parent_id, parent_type=parent_type).order_by(HeadingLesson.position).all(),
            image_content=db.query(ImageLesson).filter_by(
                parent_id=parent_id, parent_type=parent_type).order_by(ImageLesson.position).all(),
            code_content=db.query(CodeLesson).filter_by(
                parent_id=parent_id, parent_type=parent_type).order_by(CodeLesson.position).all(),
            hint_content=db.query(HintLesson).filter_by(
                parent_id=parent_id, parent_type=parent_type).order_by(HintLesson.position).all(),
            callout_content=db.query(CalloutLesson).filter_by(
                parent_id=parent_id, parent_type=parent_type).order_by(CalloutLesson.position).all(),
        )
