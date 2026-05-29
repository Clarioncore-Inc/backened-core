from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.schema import BaseSchema


class AppSettingsResponse(BaseSchema):
    id: UUID
    app_name: str
    logo: Optional[str] = None
    contacts: Optional[str] = None
    email: Optional[str] = None
    iq_test_price: float
    created_at: datetime
    updated_at: datetime


class AppSettingsUpdateRequest(BaseSchema):
    app_name: Optional[str] = None
    logo: Optional[str] = None
    contacts: Optional[str] = None
    email: Optional[str] = None
    iq_test_price: Optional[float] = None