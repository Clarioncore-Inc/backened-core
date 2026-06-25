from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

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


# ── Genius Profiles ────────────────────────────────────────────────────────────

class GeniusProfileType(str, Enum):
    historical = "historical"
    fictional = "fictional"
    public_intellectual = "public_intellectual"


class GeniusPublicationStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class GeniusCreate(BaseSchema):
    id: Optional[str] = None  # slug-style; auto-generated from full_name if omitted
    full_name: str
    iq_score: Optional[int] = None
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    birth_place: str
    zodiac_sign: Optional[str] = None
    biography: str
    short_description: str
    era: str
    is_historical: bool = True
    is_fictional: bool = False
    profile_type: GeniusProfileType = GeniusProfileType.historical
    publication_status: GeniusPublicationStatus = GeniusPublicationStatus.draft
    editorial_note: Optional[str] = None
    source_url: Optional[str] = None
    profile_image_url: Optional[str] = None


class GeniusUpdate(BaseSchema):
    full_name: Optional[str] = None
    iq_score: Optional[int] = None
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    birth_place: Optional[str] = None
    zodiac_sign: Optional[str] = None
    biography: Optional[str] = None
    short_description: Optional[str] = None
    era: Optional[str] = None
    is_historical: Optional[bool] = None
    is_fictional: Optional[bool] = None
    profile_type: Optional[GeniusProfileType] = None
    publication_status: Optional[GeniusPublicationStatus] = None
    editorial_note: Optional[str] = None
    source_url: Optional[str] = None
    profile_image_url: Optional[str] = None


class GeniusResponse(BaseSchema):
    id: str
    slug: str
    full_name: str
    iq_score: Optional[int]
    iq_score_label: str
    iq_score_note: str
    birth_date: Optional[str]
    death_date: Optional[str]
    birth_place: str
    zodiac_sign: Optional[str]
    biography: str
    short_description: str
    era: str
    profile_type: str
    is_historical: bool
    is_fictional: bool
    editorial_note: str
    publication_status: str
    source_url: Optional[str]
    profile_image_url: Optional[str]
    created_at: datetime
    updated_at: datetime


class GeniusListResponse(BaseSchema):
    items: List[GeniusResponse]
    total: int


class GeniusStatusUpdate(BaseSchema):
    publication_status: GeniusPublicationStatus

