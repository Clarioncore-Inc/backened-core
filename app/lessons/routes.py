from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.lessons.models import (
    CalloutLesson,
    CodeLesson,
    HeadingLesson,
    HintLesson,
    ImageLesson,
    InteractiveLesson,
    InteractiveStep,
    Lesson,
    ProblemLesson,
    ProblemTestCase,
    QuizLesson,
    QuizQuestion,
    QuizQuestionOption,
    Section,
    TextLesson,
    TextLessonAttachment,
    VideoLesson,
)
from app.attachment.models import Attachment
from app.lessons.schemas import (
    BookmarkResponse,
    CalloutLessonCreate,
    CalloutLessonResponse,
    CalloutLessonUpdate,
    CodeLessonCreate,
    CodeLessonResponse,
    CodeLessonUpdate,
    CommentCreate,
    CommentResponse,
    HeadingLessonCreate,
    HeadingLessonResponse,
    HeadingLessonUpdate,
    HintLessonCreate,
    HintLessonResponse,
    HintLessonUpdate,
    ImageLessonCreate,
    ImageLessonResponse,
    ImageLessonUpdate,
    InteractiveLessonCreate,
    InteractiveLessonResponse,
    InteractiveLessonUpdate,
    LessonCreate,
    LessonResponse,
    LessonUpdate,
    ProblemLessonCreate,
    ProblemLessonResponse,
    ProblemLessonUpdate,
    QuizLessonCreate,
    QuizLessonResponse,
    QuizLessonUpdate,
    SectionCreate,
    SectionResponse,
    SectionUpdate,
    TextLessonCreate,
    TextLessonResponse,
    TextLessonUpdate,
    VideoLessonCreate,
    VideoLessonResponse,
    VideoLessonUpdate,
)
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User

sections_router = APIRouter(prefix="/sections", tags=["sections"])


@cbv(sections_router)
class SectionsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @sections_router.post("/", response_model=SectionResponse, status_code=201)
    def create_section(self, payload: SectionCreate):
        data = payload.model_dump(exclude={"attachment_ids"})
        section = service_locator.general_service.create(
            db=self.db, data=data, model=Section)
        if payload.attachment_ids:
            section.attachments = self.db.query(Attachment).filter(
                Attachment.id.in_(payload.attachment_ids)).all()
            self.db.commit()
            self.db.refresh(section)
        return section

    @sections_router.get("/{id}", response_model=SectionResponse)
    def get_section(self, id: UUID):
        section = service_locator.lesson_service.get_section_with_lessons(
            db=self.db, section_id=id
        )
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        return section

    @sections_router.put("/{id}", response_model=SectionResponse)
    def update_section(self, id: UUID, payload: SectionUpdate):
        data = payload.model_dump(
            exclude_unset=True, exclude={"attachment_ids"})
        section = service_locator.general_service.update_data(
            db=self.db, key=id, data=data, model=Section
        )
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        if payload.attachment_ids is not None:
            section.attachments = self.db.query(Attachment).filter(
                Attachment.id.in_(payload.attachment_ids)).all()
            self.db.commit()
            self.db.refresh(section)
        return section

    @sections_router.delete("/{id}", status_code=204)
    def delete_section(self, id: UUID):
        section = service_locator.general_service.get(
            db=self.db, key=id, model=Section)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        service_locator.general_service.delete(
            db=self.db, key=id, model=Section)


router = APIRouter(prefix="/lessons", tags=["lessons"])


@cbv(router)
class LessonsView:
    db: Session = Depends(get_db)

    @router.post("/", response_model=LessonResponse, status_code=201)
    def create_lesson(
        self,
        payload: LessonCreate,
        current_user: User = Depends(get_current_active_user),
    ):
        data = payload.model_dump(exclude_unset=True)
        return service_locator.lesson_service.create_lesson_with_content(
            db=self.db, lesson_data=data
        )

    @router.get("/{id}", response_model=LessonResponse)
    def get_lesson(self, id: UUID):
        lesson = service_locator.lesson_service.get_lesson_detail(
            db=self.db, lesson_id=id
        )
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return lesson

    @router.put("/{id}", response_model=LessonResponse)
    @router.patch("/{id}", response_model=LessonResponse)
    def update_lesson(
        self,
        id: UUID,
        payload: LessonUpdate,
        current_user: User = Depends(get_current_active_user),
    ):
        lesson = service_locator.lesson_service.update_lesson_with_content(
            db=self.db,
            lesson_id=id,
            lesson_data=payload.model_dump(exclude_unset=True),
        )
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return lesson

    @router.delete("/{id}", status_code=204)
    def delete_lesson(
        self,
        id: UUID,
        current_user: User = Depends(get_current_active_user),
    ):
        lesson = service_locator.general_service.get(
            db=self.db, key=id, model=Lesson)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        service_locator.general_service.delete(
            db=self.db, key=id, model=Lesson)

    @router.get("/{id}/comments", response_model=List[CommentResponse])
    def get_comments(self, id: UUID):
        return service_locator.lesson_service.get_comments(db=self.db, lesson_id=id)

    @router.post("/{id}/like")
    def like_lesson(self, id: UUID, current_user: User = Depends(get_current_active_user)):
        lesson = service_locator.lesson_service.add_like(
            db=self.db, user_id=current_user.id, lesson_id=id
        )
        return {"success": True, "likes": lesson.like_count if lesson else 0}

    @router.delete("/{id}/like")
    def unlike_lesson(self, id: UUID, current_user: User = Depends(get_current_active_user)):
        lesson = service_locator.lesson_service.remove_like(
            db=self.db, user_id=current_user.id, lesson_id=id
        )
        return {"success": True, "likes": lesson.like_count if lesson else 0}

    @router.post("/{id}/bookmark", response_model=BookmarkResponse)
    def bookmark_lesson(self, id: UUID, current_user: User = Depends(get_current_active_user)):
        return service_locator.lesson_service.add_bookmark(
            db=self.db, user_id=current_user.id, lesson_id=id
        )


bookmarks_router = APIRouter(prefix="/bookmarks", tags=["lessons"])


@cbv(bookmarks_router)
class BookmarksView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @bookmarks_router.get("/", response_model=List[BookmarkResponse])
    def get_bookmarks(self):
        return service_locator.lesson_service.get_bookmarks(
            db=self.db, user_id=self.current_user.id
        )


comments_router = APIRouter(prefix="/comments", tags=["lessons"])


@cbv(comments_router)
class CommentsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @comments_router.post("/", response_model=CommentResponse, status_code=201)
    def add_comment(self, payload: CommentCreate):
        data = payload.model_dump()
        return service_locator.lesson_service.add_comment(
            db=self.db, user_id=self.current_user.id, data=data
        )


video_lessons_router = APIRouter(
    prefix="/video-lessons", tags=["lesson contents"])


@cbv(video_lessons_router)
class VideoLessonsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @video_lessons_router.post("/", response_model=VideoLessonResponse, status_code=201)
    def create_video_lesson(self, payload: VideoLessonCreate):
        data = payload.model_dump()
        if data.get("parent_id") is None:
            data["parent_type"] = "lesson"
        else:
            data["parent_type"] = service_locator.lesson_service.determine_parent_type(
                self.db, data["parent_id"])
        return service_locator.general_service.create(db=self.db, data=data, model=VideoLesson)

    # @video_lessons_router.get("/{id}", response_model=VideoLessonResponse)
    # def get_video_lesson(self, id: UUID):
    #     lesson = service_locator.general_service.get(
    #         db=self.db, key=id, model=VideoLesson)
    #     if not lesson:
    #         raise HTTPException(
    #             status_code=404, detail="Video lesson not found")
    #     lesson.children = service_locator.lesson_service.get_children(
    #         self.db, parent_id=lesson.id, parent_type="video_lesson")
    #     return lesson

    @video_lessons_router.put("/{id}", response_model=VideoLessonResponse)
    def update_video_lesson(self, id: UUID, payload: VideoLessonUpdate):
        lesson = service_locator.general_service.update_data(
            db=self.db,
            key=id,
            data=payload.model_dump(exclude_unset=True),
            model=VideoLesson,
        )
        if not lesson:
            raise HTTPException(
                status_code=404, detail="Video lesson not found")
        return lesson

    @video_lessons_router.delete("/{id}", status_code=204)
    def delete_video_lesson(self, id: UUID):
        deleted = service_locator.general_service.delete(
            db=self.db, key=id, model=VideoLesson)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Video lesson not found")


text_lessons_router = APIRouter(
    prefix="/text-lessons", tags=["lesson contents"])


@cbv(text_lessons_router)
class TextLessonsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    def _build_text_attachments(self, attachment_ids: List[UUID] | None) -> List[TextLessonAttachment]:
        if not attachment_ids:
            return []
        attachments = self.db.query(Attachment).filter(
            Attachment.id.in_(attachment_ids)).all()
        return [TextLessonAttachment(attachment=attachment) for attachment in attachments]

    @text_lessons_router.post("/", response_model=TextLessonResponse, status_code=201)
    def create_text_lesson(self, payload: TextLessonCreate):
        data = payload.model_dump(exclude={"attachment_ids"})
        if data.get("parent_id") is None:
            data["parent_type"] = "lesson"
        else:
            data["parent_type"] = service_locator.lesson_service.determine_parent_type(
                self.db, data["parent_id"])
        lesson = service_locator.general_service.create(
            db=self.db, data=data, model=TextLesson)
        if payload.attachment_ids:
            lesson.attachments = self._build_text_attachments(
                payload.attachment_ids)
            self.db.commit()
            self.db.refresh(lesson)
        return lesson

    # @text_lessons_router.get("/{id}", response_model=TextLessonResponse)
    # def get_text_lesson(self, id: UUID):
    #     lesson = service_locator.general_service.get(
    #         db=self.db, key=id, model=TextLesson)
    #     if not lesson:
    #         raise HTTPException(
    #             status_code=404, detail="Text lesson not found")
    #     lesson.children = service_locator.lesson_service.get_children(
    #         self.db, parent_id=lesson.id, parent_type="text_lesson")
    #     return lesson

    @text_lessons_router.put("/{id}", response_model=TextLessonResponse)
    def update_text_lesson(self, id: UUID, payload: TextLessonUpdate):
        lesson = service_locator.general_service.update_data(
            db=self.db,
            key=id,
            data=payload.model_dump(
                exclude_unset=True, exclude={"attachment_ids"}),
            model=TextLesson,
        )
        if not lesson:
            raise HTTPException(
                status_code=404, detail="Text lesson not found")
        if payload.attachment_ids is not None:
            lesson.attachments = self._build_text_attachments(
                payload.attachment_ids)
            self.db.commit()
            self.db.refresh(lesson)
        return lesson

    @text_lessons_router.delete("/{id}", status_code=204)
    def delete_text_lesson(self, id: UUID):
        deleted = service_locator.general_service.delete(
            db=self.db, key=id, model=TextLesson)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Text lesson not found")


quiz_lessons_router = APIRouter(
    prefix="/quiz-lessons", tags=["lesson contents"])


@cbv(quiz_lessons_router)
class QuizLessonsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    def _attach_quiz_questions(self, quiz: QuizLesson, questions: list) -> None:
        for question_payload in questions:
            question_data = question_payload.model_dump(exclude={"options"})
            question = QuizQuestion(quiz=quiz, **question_data)
            for option_payload in question_payload.options:
                option_data = option_payload.model_dump()
                question.options.append(QuizQuestionOption(**option_data))
            quiz.questions.append(question)

    @quiz_lessons_router.post("/", response_model=QuizLessonResponse, status_code=201)
    def create_quiz_lesson(self, payload: QuizLessonCreate):
        data = payload.model_dump(exclude={"questions"})
        if data.get("parent_id") is None:
            data["parent_type"] = "lesson"
        else:
            data["parent_type"] = service_locator.lesson_service.determine_parent_type(
                self.db, data["parent_id"])
        lesson = QuizLesson(**data)
        self.db.add(lesson)
        self.db.flush()
        self._attach_quiz_questions(lesson, payload.questions)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    # @quiz_lessons_router.get("/{id}", response_model=QuizLessonResponse)
    # def get_quiz_lesson(self, id: UUID):
    #     lesson = service_locator.general_service.get(
    #         db=self.db, key=id, model=QuizLesson)
    #     if not lesson:
    #         raise HTTPException(
    #             status_code=404, detail="Quiz lesson not found")
    #     lesson.children = service_locator.lesson_service.get_children(
    #         self.db, parent_id=lesson.id, parent_type="quiz_lesson")
    #     return lesson

    @quiz_lessons_router.put("/{id}", response_model=QuizLessonResponse)
    def update_quiz_lesson(self, id: UUID, payload: QuizLessonUpdate):
        lesson = self.db.query(QuizLesson).filter(QuizLesson.id == id).first()
        if not lesson:
            raise HTTPException(
                status_code=404, detail="Quiz lesson not found")
        data = payload.model_dump(exclude_unset=True, exclude={"questions"})
        for field, value in data.items():
            setattr(lesson, field, value)
        if payload.questions is not None:
            lesson.questions = []
            self.db.flush()
            self._attach_quiz_questions(lesson, payload.questions)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    @quiz_lessons_router.delete("/{id}", status_code=204)
    def delete_quiz_lesson(self, id: UUID):
        deleted = service_locator.general_service.delete(
            db=self.db, key=id, model=QuizLesson)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Quiz lesson not found")


interactive_lessons_router = APIRouter(
    prefix="/interactive-lessons", tags=["lesson contents"])


@cbv(interactive_lessons_router)
class InteractiveLessonsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    def _attach_interactive_steps(self, lesson: InteractiveLesson, steps: list) -> None:
        for step_payload in steps:
            step_data = step_payload.model_dump()
            lesson.steps.append(InteractiveStep(**step_data))

    @interactive_lessons_router.post("/", response_model=InteractiveLessonResponse, status_code=201)
    def create_interactive_lesson(self, payload: InteractiveLessonCreate):
        data = payload.model_dump(exclude={"steps"})
        if data.get("parent_id") is None:
            data["parent_type"] = "lesson"
        else:
            data["parent_type"] = service_locator.lesson_service.determine_parent_type(
                self.db, data["parent_id"])
        lesson = InteractiveLesson(**data)
        self.db.add(lesson)
        self.db.flush()
        self._attach_interactive_steps(lesson, payload.steps)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    # @interactive_lessons_router.get("/{id}", response_model=InteractiveLessonResponse)
    # def get_interactive_lesson(self, id: UUID):
    #     lesson = service_locator.general_service.get(
    #         db=self.db, key=id, model=InteractiveLesson)
    #     if not lesson:
    #         raise HTTPException(
    #             status_code=404, detail="Interactive lesson not found")
    #     lesson.children = service_locator.lesson_service.get_children(
    #         self.db, parent_id=lesson.id, parent_type="interactive_lesson")
    #     return lesson

    @interactive_lessons_router.put("/{id}", response_model=InteractiveLessonResponse)
    def update_interactive_lesson(self, id: UUID, payload: InteractiveLessonUpdate):
        lesson = self.db.query(InteractiveLesson).filter(
            InteractiveLesson.id == id).first()
        if not lesson:
            raise HTTPException(
                status_code=404, detail="Interactive lesson not found")
        data = payload.model_dump(exclude_unset=True, exclude={"steps"})
        for field, value in data.items():
            setattr(lesson, field, value)
        if payload.steps is not None:
            lesson.steps = []
            self.db.flush()
            self._attach_interactive_steps(lesson, payload.steps)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    @interactive_lessons_router.delete("/{id}", status_code=204)
    def delete_interactive_lesson(self, id: UUID):
        deleted = service_locator.general_service.delete(
            db=self.db, key=id, model=InteractiveLesson)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Interactive lesson not found")


problem_lessons_router = APIRouter(
    prefix="/problem-lessons", tags=["lesson contents"])


@cbv(problem_lessons_router)
class ProblemLessonsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    def _attach_problem_test_cases(self, lesson: ProblemLesson, test_cases: list) -> None:
        for test_case_payload in test_cases:
            test_case_data = test_case_payload.model_dump()
            lesson.test_cases.append(ProblemTestCase(**test_case_data))

    @problem_lessons_router.post("/", response_model=ProblemLessonResponse, status_code=201)
    def create_problem_lesson(self, payload: ProblemLessonCreate):
        data = payload.model_dump(exclude={"test_cases"})
        if data.get("parent_id") is None:
            data["parent_type"] = "lesson"
        else:
            data["parent_type"] = service_locator.lesson_service.determine_parent_type(
                self.db, data["parent_id"])
        lesson = ProblemLesson(**data)
        self.db.add(lesson)
        self.db.flush()
        self._attach_problem_test_cases(lesson, payload.test_cases)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    # @problem_lessons_router.get("/{id}", response_model=ProblemLessonResponse)
    # def get_problem_lesson(self, id: UUID):
    #     lesson = service_locator.general_service.get(
    #         db=self.db, key=id, model=ProblemLesson)
    #     if not lesson:
    #         raise HTTPException(
    #             status_code=404, detail="Problem lesson not found")
    #     lesson.children = service_locator.lesson_service.get_children(
    #         self.db, parent_id=lesson.id, parent_type="problem_lesson")
    #     return lesson

    @problem_lessons_router.put("/{id}", response_model=ProblemLessonResponse)
    def update_problem_lesson(self, id: UUID, payload: ProblemLessonUpdate):
        lesson = self.db.query(ProblemLesson).filter(
            ProblemLesson.id == id).first()
        if not lesson:
            raise HTTPException(
                status_code=404, detail="Problem lesson not found")
        data = payload.model_dump(exclude_unset=True, exclude={"test_cases"})
        for field, value in data.items():
            setattr(lesson, field, value)
        if payload.test_cases is not None:
            lesson.test_cases = []
            self.db.flush()
            self._attach_problem_test_cases(lesson, payload.test_cases)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    @problem_lessons_router.delete("/{id}", status_code=204)
    def delete_problem_lesson(self, id: UUID):
        deleted = service_locator.general_service.delete(
            db=self.db, key=id, model=ProblemLesson)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Problem lesson not found")


heading_lessons_router = APIRouter(
    prefix="/heading-lessons", tags=["lesson contents"])


@cbv(heading_lessons_router)
class HeadingLessonsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @heading_lessons_router.post("/", response_model=HeadingLessonResponse, status_code=201)
    def create_heading_lesson(self, payload: HeadingLessonCreate):
        data = payload.model_dump()
        if data.get("parent_id") is None:
            data["parent_type"] = "lesson"
        else:
            data["parent_type"] = service_locator.lesson_service.determine_parent_type(
                self.db, data["parent_id"])
        return service_locator.general_service.create(
            db=self.db, data=data, model=HeadingLesson
        )

    # @heading_lessons_router.get("/{id}", response_model=HeadingLessonResponse)
    # def get_heading_lesson(self, id: UUID):
    #     lesson = service_locator.general_service.get(
    #         db=self.db, key=id, model=HeadingLesson)
    #     if not lesson:
    #         raise HTTPException(
    #             status_code=404, detail="Heading lesson not found")
    #     lesson.children = service_locator.lesson_service.get_children(
    #         self.db, parent_id=lesson.id, parent_type="heading_lesson")
    #     return lesson

    @heading_lessons_router.put("/{id}", response_model=HeadingLessonResponse)
    def update_heading_lesson(self, id: UUID, payload: HeadingLessonUpdate):
        lesson = service_locator.general_service.update_data(
            db=self.db, key=id, data=payload.model_dump(exclude_unset=True), model=HeadingLesson
        )
        if not lesson:
            raise HTTPException(
                status_code=404, detail="Heading lesson not found")
        return lesson

    @heading_lessons_router.delete("/{id}", status_code=204)
    def delete_heading_lesson(self, id: UUID):
        deleted = service_locator.general_service.delete(
            db=self.db, key=id, model=HeadingLesson)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Heading lesson not found")


image_lessons_router = APIRouter(
    prefix="/image-lessons", tags=["lesson contents"])


@cbv(image_lessons_router)
class ImageLessonsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @image_lessons_router.post("/", response_model=ImageLessonResponse, status_code=201)
    def create_image_lesson(self, payload: ImageLessonCreate):
        data = payload.model_dump()
        if data.get("parent_id") is None:
            data["parent_type"] = "lesson"
        else:
            data["parent_type"] = service_locator.lesson_service.determine_parent_type(
                self.db, data["parent_id"])
        return service_locator.general_service.create(
            db=self.db, data=data, model=ImageLesson
        )

    # @image_lessons_router.get("/{id}", response_model=ImageLessonResponse)
    # def get_image_lesson(self, id: UUID):
    #     lesson = service_locator.general_service.get(
    #         db=self.db, key=id, model=ImageLesson)
    #     if not lesson:
    #         raise HTTPException(
    #             status_code=404, detail="Image lesson not found")
    #     lesson.children = service_locator.lesson_service.get_children(
    #         self.db, parent_id=lesson.id, parent_type="image_lesson")
    #     return lesson

    @image_lessons_router.put("/{id}", response_model=ImageLessonResponse)
    def update_image_lesson(self, id: UUID, payload: ImageLessonUpdate):
        lesson = service_locator.general_service.update_data(
            db=self.db, key=id, data=payload.model_dump(exclude_unset=True), model=ImageLesson
        )
        if not lesson:
            raise HTTPException(
                status_code=404, detail="Image lesson not found")
        return lesson

    @image_lessons_router.delete("/{id}", status_code=204)
    def delete_image_lesson(self, id: UUID):
        deleted = service_locator.general_service.delete(
            db=self.db, key=id, model=ImageLesson)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Image lesson not found")


code_lessons_router = APIRouter(
    prefix="/code-lessons", tags=["lesson contents"])


@cbv(code_lessons_router)
class CodeLessonsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @code_lessons_router.post("/", response_model=CodeLessonResponse, status_code=201)
    def create_code_lesson(self, payload: CodeLessonCreate):
        data = payload.model_dump()
        if data.get("parent_id") is None:
            data["parent_type"] = "lesson"
        else:
            data["parent_type"] = service_locator.lesson_service.determine_parent_type(
                self.db, data["parent_id"])
        return service_locator.general_service.create(
            db=self.db, data=data, model=CodeLesson
        )

    # @code_lessons_router.get("/{id}", response_model=CodeLessonResponse)
    # def get_code_lesson(self, id: UUID):
    #     lesson = service_locator.general_service.get(
    #         db=self.db, key=id, model=CodeLesson)
    #     if not lesson:
    #         raise HTTPException(
    #             status_code=404, detail="Code lesson not found")
    #     lesson.children = service_locator.lesson_service.get_children(
    #         self.db, parent_id=lesson.id, parent_type="code_lesson")
    #     return lesson

    @code_lessons_router.put("/{id}", response_model=CodeLessonResponse)
    def update_code_lesson(self, id: UUID, payload: CodeLessonUpdate):
        lesson = service_locator.general_service.update_data(
            db=self.db, key=id, data=payload.model_dump(exclude_unset=True), model=CodeLesson
        )
        if not lesson:
            raise HTTPException(
                status_code=404, detail="Code lesson not found")
        return lesson

    @code_lessons_router.delete("/{id}", status_code=204)
    def delete_code_lesson(self, id: UUID):
        deleted = service_locator.general_service.delete(
            db=self.db, key=id, model=CodeLesson)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Code lesson not found")


hint_lessons_router = APIRouter(
    prefix="/hint-lessons", tags=["lesson contents"])


@cbv(hint_lessons_router)
class HintLessonsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @hint_lessons_router.post("/", response_model=HintLessonResponse, status_code=201)
    def create_hint_lesson(self, payload: HintLessonCreate):
        data = payload.model_dump()
        if data.get("parent_id") is None:
            data["parent_type"] = "lesson"
        else:
            data["parent_type"] = service_locator.lesson_service.determine_parent_type(
                self.db, data["parent_id"])
        return service_locator.general_service.create(
            db=self.db, data=data, model=HintLesson
        )

    # @hint_lessons_router.get("/{id}", response_model=HintLessonResponse)
    # def get_hint_lesson(self, id: UUID):
    #     lesson = service_locator.general_service.get(
    #         db=self.db, key=id, model=HintLesson)
    #     if not lesson:
    #         raise HTTPException(
    #             status_code=404, detail="Hint lesson not found")
    #     lesson.children = service_locator.lesson_service.get_children(
    #         self.db, parent_id=lesson.id, parent_type="hint_lesson")
    #     return lesson

    @hint_lessons_router.put("/{id}", response_model=HintLessonResponse)
    def update_hint_lesson(self, id: UUID, payload: HintLessonUpdate):
        lesson = service_locator.general_service.update_data(
            db=self.db, key=id, data=payload.model_dump(exclude_unset=True), model=HintLesson
        )
        if not lesson:
            raise HTTPException(
                status_code=404, detail="Hint lesson not found")
        return lesson

    @hint_lessons_router.delete("/{id}", status_code=204)
    def delete_hint_lesson(self, id: UUID):
        deleted = service_locator.general_service.delete(
            db=self.db, key=id, model=HintLesson)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Hint lesson not found")


callout_lessons_router = APIRouter(
    prefix="/callout-lessons", tags=["lesson contents"])


@cbv(callout_lessons_router)
class CalloutLessonsView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @callout_lessons_router.post("/", response_model=CalloutLessonResponse, status_code=201)
    def create_callout_lesson(self, payload: CalloutLessonCreate):
        data = payload.model_dump()
        if data.get("parent_id") is None:
            data["parent_type"] = "lesson"
        else:
            data["parent_type"] = service_locator.lesson_service.determine_parent_type(
                self.db, data["parent_id"])
        return service_locator.general_service.create(
            db=self.db, data=data, model=CalloutLesson
        )

    # @callout_lessons_router.get("/{id}", response_model=CalloutLessonResponse)
    # def get_callout_lesson(self, id: UUID):
    #     lesson = service_locator.general_service.get(
    #         db=self.db, key=id, model=CalloutLesson)
    #     if not lesson:
    #         raise HTTPException(
    #             status_code=404, detail="Callout lesson not found")
    #     lesson.children = service_locator.lesson_service.get_children(
    #         self.db, parent_id=lesson.id, parent_type="callout_lesson")
    #     return lesson

    @callout_lessons_router.put("/{id}", response_model=CalloutLessonResponse)
    def update_callout_lesson(self, id: UUID, payload: CalloutLessonUpdate):
        lesson = service_locator.general_service.update_data(
            db=self.db, key=id, data=payload.model_dump(exclude_unset=True), model=CalloutLesson
        )
        if not lesson:
            raise HTTPException(
                status_code=404, detail="Callout lesson not found")
        return lesson

    @callout_lessons_router.delete("/{id}", status_code=204)
    def delete_callout_lesson(self, id: UUID):
        deleted = service_locator.general_service.delete(
            db=self.db, key=id, model=CalloutLesson)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Callout lesson not found")
