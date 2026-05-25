from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.accounts.models import User
from app.authentication.utils import get_current_active_user
from app.core.dependency_injection import service_locator
from app.dependencies import get_db
from app.notes.models import Note
from app.notes.schemas import NoteCreate, NotePinUpdate, NoteResponse, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


@cbv(router)
class NotesView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    def _get_owned_note(self, id: UUID) -> Note:
        note = service_locator.general_service.get(db=self.db, key=id, model=Note)
        if not note or note.user_id != self.current_user.id:
            raise HTTPException(status_code=404, detail="Note not found")
        return note

    @router.get("/", response_model=List[NoteResponse])
    def list_notes(
        self,
        course_id: Optional[UUID] = None,
        lesson_id: Optional[UUID] = None,
        pinned: Optional[bool] = None,
    ):
        filters = {"user_id": self.current_user.id}
        if course_id is not None:
            filters["course_id"] = course_id
        if lesson_id is not None:
            filters["lesson_id"] = lesson_id
        if pinned is not None:
            filters["is_pinned"] = pinned

        notes = service_locator.general_service.filter_data(
            db=self.db,
            model=Note,
            filters=filters,
        )
        return sorted(
            notes,
            key=lambda note: (note.is_pinned, note.updated_at or note.created_at),
            reverse=True,
        )

    @router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
    def create_note(self, payload: NoteCreate):
        data = payload.model_dump()
        data["user_id"] = self.current_user.id
        return service_locator.general_service.create(db=self.db, data=data, model=Note)

    @router.get("/{id}", response_model=NoteResponse)
    def get_note(self, id: UUID):
        return self._get_owned_note(id)

    @router.put("/{id}", response_model=NoteResponse)
    def update_note(self, id: UUID, payload: NoteUpdate):
        self._get_owned_note(id)
        note = service_locator.general_service.update_data(
            db=self.db,
            key=id,
            data=payload.model_dump(exclude_unset=True),
            model=Note,
        )
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note

    @router.patch("/{id}/pin", response_model=NoteResponse)
    def pin_note(self, id: UUID, payload: NotePinUpdate):
        self._get_owned_note(id)
        note = service_locator.general_service.update_data(
            db=self.db,
            key=id,
            data=payload.model_dump(),
            model=Note,
        )
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note

    @router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_note(self, id: UUID):
        self._get_owned_note(id)
        deleted = service_locator.general_service.delete(db=self.db, key=id, model=Note)
        if not deleted:
            raise HTTPException(status_code=404, detail="Note not found")
