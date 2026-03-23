from typing import Optional
from pydantic import EmailStr
from app.core.schema import BaseSchema
from uuid import UUID
from app.accounts.schemas import UserResponse


class SignupRequest(BaseSchema):
    email: EmailStr
    password: str
    full_name: str
    role: str = "learner"
    org_id: Optional[UUID] = None


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str


class OTPLoginRequest(BaseSchema):
    email: EmailStr
    otp: str


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SignupResponse(BaseSchema):
    success: bool
    user: UserResponse
