from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import EmailStr
from app.core.schema import BaseSchema


class UserBase(BaseSchema):
    email: EmailStr
    full_name: str
    role: str = "learner"
    org_id: Optional[UUID] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseSchema):
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    xp: int
    streak: int
    is_active: bool
    is_suspended: bool
    created_at: datetime
    updated_at: datetime


class UserPublic(BaseSchema):
    """Safe subset exposed in leaderboard / public views."""
    id: UUID
    full_name: str
    role: str
    xp: int
    streak: int
    avatar: Optional[str] = None

