from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime
from app.core.schema import BaseSchema


class PlatformAnalyticsResponse(BaseSchema):
    total_users: int
    total_courses: int
    total_enrollments: int
    total_revenue: float


class RoleUpdateRequest(BaseSchema):
    role: str


class StatusUpdateRequest(BaseSchema):
    suspended: bool


class PlatformSettings(BaseSchema):
    platform_name: str = "CerebroLearn"
    maintenance_mode: bool = False
    allow_signups: bool = True
    default_currency: str = "USD"
    platform_fee_rate: float = 0.20
    extra: Optional[Dict[str, Any]] = None


class SettingsUpdateRequest(BaseSchema):
    platform_name: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    allow_signups: Optional[bool] = None
    default_currency: Optional[str] = None
    platform_fee_rate: Optional[float] = None
    extra: Optional[Dict[str, Any]] = None


class SessionTypeCreate(BaseSchema):
    name: str
    price: float
    description: Optional[str] = None


class SessionTypeUpdate(BaseSchema):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None


class SessionTypeResponse(BaseSchema):
    id: UUID
    name: str
    price: float
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MeetingConfigUpsert(BaseSchema):
    name: str
    link: str
    password: Optional[str] = None


class MeetingConfigResponse(BaseSchema):
    id: UUID
    name: str
    link: str
    password: Optional[str] = None
    created_at: datetime
    updated_at: datetime

