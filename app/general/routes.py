from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependency_injection import service_locator
from app.dependencies import get_db
from app.general.schemas import AppSettingsResponse

router = APIRouter(prefix="/general", tags=["general"])


@router.get("/app-settings", response_model=AppSettingsResponse)
def get_app_settings(db: Session = Depends(get_db)):
    return service_locator.general_service.get_app_settings(db=db)