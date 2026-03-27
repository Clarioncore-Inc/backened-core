from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.progress.schemas import ProgressResponse, ProgressSave
from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User

router = APIRouter(prefix="/progress", tags=["progress"])


@cbv(router)
class ProgressView:
    db: Session = Depends(get_db)
    current_user: User = Depends(get_current_active_user)

    @router.post("/", response_model=ProgressResponse)
    def save_progress(self, payload: ProgressSave):
        data = payload.model_dump()
        return service_locator.progress_service.save_progress(
            db=self.db, user_id=self.current_user.id, data=data
        )

    @router.get("/lesson/{lesson_id}", response_model=ProgressResponse)
    def get_progress(self, lesson_id: UUID):
        record = service_locator.progress_service.get_progress(
            db=self.db, user_id=self.current_user.id, lesson_id=lesson_id
        )
        if not record:
            raise HTTPException(status_code=404, detail="Progress not found")
        return record
