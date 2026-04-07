from typing import Any, Dict, Optional
from uuid import UUID
from datetime import date, datetime
from app.core.schema import BaseSchema
from enum import Enum


class AttachmentStartRequest(BaseSchema):
    class CreateType(Enum):
        POST = "post"
        PUT = "put"
    file_type: str
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    create_type: Optional[CreateType] = None


class AttachmentStartResponse(BaseSchema):
    id: UUID
    url: str
    fields: Optional[Dict[str, Any]] = None


class AttachmentFinishRequest(BaseSchema):
    thumbnail: Optional[str] = None


class AttachmentUpdate(BaseSchema):
    url: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    s3_key: Optional[str] = None
    thumbnail: Optional[str] = None
    upload_finished_at: Optional[date] = None


class AttachmentResponse(BaseSchema):
    id: UUID
    url: str
    created_by: Optional[UUID] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    s3_key: Optional[str] = None
    thumbnail: Optional[str] = None
    upload_finished_at: Optional[date] = None
    created_at: datetime
    updated_at: datetime
