from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.attachment.models import Attachment
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
    ProblemTestCase,
    QuizQuestion,
    QuizQuestionOption,
    QuizLesson,
    # QuizQuestion,
    Section,
    TextLessonAttachment,
    TextLesson,
    # TextLessonAttachment,
    VideoLesson,
    InteractiveStep,
    LessonContentMixin,

)
from app.lessons.schemas.lesson_contents import ChildContentResponse


class LessonService:
    CONTENT_MODELS = {
        "video_content": (VideoLesson, LessonContentMixin.ParentType.VIDEO_LESSON),
        "text_content": (TextLesson, LessonContentMixin.ParentType.TEXT_LESSON),
        "quiz_content": (QuizLesson, LessonContentMixin.ParentType.QUIZ_LESSON),
        "interactive_content": (
            InteractiveLesson, LessonContentMixin.ParentType.INTERACTIVE_LESSON),
        "problem_content": (ProblemLesson, LessonContentMixin.ParentType.PROBLEM_LESSON),
        "heading_content": (HeadingLesson, LessonContentMixin.ParentType.HEADING_LESSON),
        "image_content": (ImageLesson, LessonContentMixin.ParentType.IMAGE_LESSON),
        "code_content": (CodeLesson, LessonContentMixin.ParentType.CODE_LESSON),
        "hint_content": (HintLesson, LessonContentMixin.ParentType.HINT_LESSON),
        "callout_content": (CalloutLesson, LessonContentMixin.ParentType.CALLOUT_LESSON),
    }

    def get_lesson_detail(self, db: Session, lesson_id) -> Optional[Lesson]:
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            return None

        for field_name, (model, parent_type) in self.CONTENT_MODELS.items():
            blocks = (
                db.query(model)
                .filter_by(lesson_id=lesson_id, parent_id=None)
                .order_by(model.position)
                .all()
            )
            self._populate_children(db, blocks, parent_type)
            setattr(lesson, field_name, blocks)

        return lesson

    def create_lesson_with_content(self, db: Session, lesson_data: Dict[str, Any]) -> Lesson:
        content_payload = self._extract_content_payload(lesson_data)
        lesson = Lesson(**lesson_data)
        db.add(lesson)
        db.flush()

        self._upsert_content_tree(
            db=db,
            lesson=lesson,
            content_payload=content_payload,
            parent_id=None,
            parent_type=LessonContentMixin.ParentType.LESSON,
        )

        db.commit()
        db.refresh(lesson)
        return self.get_lesson_detail(db, lesson.id)

    def update_lesson_with_content(
        self, db: Session, lesson_id: UUID, lesson_data: Dict[str, Any]
    ) -> Optional[Lesson]:
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            return None

        content_payload = self._extract_content_payload(lesson_data)

        for field, value in lesson_data.items():
            if value is not None:
                setattr(lesson, field, value)

        self._upsert_content_tree(
            db=db,
            lesson=lesson,
            content_payload=content_payload,
            parent_id=None,
            parent_type=LessonContentMixin.ParentType.LESSON,
        )

        db.commit()
        db.refresh(lesson)
        return self.get_lesson_detail(db, lesson.id)

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
        checks = list(self.CONTENT_MODELS.values())
        for model, type_str in checks:
            if db.query(model).filter_by(id=parent_id).first():
                return type_str
        raise HTTPException(
            status_code=400, detail="Invalid parent_id — no matching content block found")

    def get_children(self, db: Session, parent_id: UUID, parent_type: str) -> ChildContentResponse:
        children = {}
        for field_name, (model, child_parent_type) in self.CONTENT_MODELS.items():
            blocks = (
                db.query(model)
                .filter_by(parent_id=parent_id, parent_type=parent_type)
                .order_by(model.position)
                .all()
            )
            self._populate_children(db, blocks, child_parent_type)
            children[field_name] = blocks
        return ChildContentResponse(**children)

    def _populate_children(self, db: Session, blocks: List[Any], parent_type: str) -> None:
        for block in blocks:
            block.children = self.get_children(
                db, parent_id=block.id, parent_type=parent_type)

    def _extract_content_payload(self, data: Dict[str, Any]) -> Dict[str, Optional[List[Dict[str, Any]]]]:
        payload = {}
        for field_name in self.CONTENT_MODELS:
            payload[field_name] = data.pop(field_name, None)
        return payload

    def _upsert_content_tree(
        self,
        db: Session,
        lesson: Lesson,
        content_payload: Dict[str, Optional[List[Dict[str, Any]]]],
        parent_id: Optional[UUID],
        parent_type: LessonContentMixin.ParentType,
    ) -> None:
        for field_name, items in content_payload.items():
            if items is None:
                continue
            self._upsert_content_items(
                db=db,
                lesson=lesson,
                field_name=field_name,
                items=items,
                parent_id=parent_id,
                parent_type=parent_type,
            )

    def _upsert_content_items(
        self,
        db: Session,
        lesson: Lesson,
        field_name: str,
        items: List[Dict[str, Any]],
        parent_id: Optional[UUID],
        parent_type: LessonContentMixin.ParentType,
    ) -> None:
        model, child_parent_type = self.CONTENT_MODELS[field_name]
        existing_items = (
            db.query(model)
            .filter_by(
                lesson_id=lesson.id,
                parent_id=parent_id,
                parent_type=parent_type,
            )
            .all()
        )
        existing_map = {item.id: item for item in existing_items}

        for item in items:
            item_data = dict(item)
            child_payload = item_data.pop("children", None) or {}
            item_id = item_data.pop("id", None)

            nested_payload = {
                "attachment_ids": item_data.pop("attachment_ids", None),
                "questions": item_data.pop("questions", None),
                "steps": item_data.pop("steps", None),
                "test_cases": item_data.pop("test_cases", None),
            }

            item_data["lesson_id"] = lesson.id
            item_data["parent_id"] = parent_id
            item_data["parent_type"] = parent_type

            instance = existing_map.get(item_id) if item_id else None
            if instance:
                for key, value in item_data.items():
                    if value is not None:
                        setattr(instance, key, value)
            else:
                instance = model(**item_data)
                db.add(instance)
                db.flush()

            self._sync_nested_content(db, instance, nested_payload)
            self._upsert_content_tree(
                db=db,
                lesson=lesson,
                content_payload=child_payload,
                parent_id=instance.id,
                parent_type=child_parent_type,
            )

    def _sync_nested_content(self, db: Session, instance: Any, nested_payload: Dict[str, Any]) -> None:
        if isinstance(instance, TextLesson) and nested_payload["attachment_ids"] is not None:
            attachment_ids = nested_payload["attachment_ids"] or []
            attachments = db.query(Attachment).filter(
                Attachment.id.in_(attachment_ids)).all()
            instance.attachments = [
                TextLessonAttachment(attachment=attachment) for attachment in attachments
            ]

        if isinstance(instance, QuizLesson) and nested_payload["questions"] is not None:
            instance.questions = []
            db.flush()
            for question_payload in nested_payload["questions"]:
                question_data = question_payload.copy()
                options_payload = question_data.pop("options", [])
                question = QuizQuestion(quiz=instance, **question_data)
                for option_payload in options_payload:
                    question.options.append(
                        QuizQuestionOption(**option_payload))
                instance.questions.append(question)

        if isinstance(instance, InteractiveLesson) and nested_payload["steps"] is not None:
            instance.steps = []
            db.flush()
            for step_payload in nested_payload["steps"]:
                instance.steps.append(InteractiveStep(**step_payload))

        if isinstance(instance, ProblemLesson) and nested_payload["test_cases"] is not None:
            instance.test_cases = []
            db.flush()
            for test_case_payload in nested_payload["test_cases"]:
                instance.test_cases.append(ProblemTestCase(**test_case_payload))
