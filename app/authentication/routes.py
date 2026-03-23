from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.accounts.models import User
from app.authentication.schemas import (
    LoginRequest,
    OTPLoginRequest,
    SignupRequest,
    SignupResponse,
    TokenResponse,
)
from app.authentication.utils import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.accounts.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@cbv(router)
class AuthView:
    db: Session = Depends(get_db)

    @router.post("/signup", response_model=SignupResponse,
                 status_code=status.HTTP_201_CREATED)
    def signup(self, payload: SignupRequest):
        existing = self.db.query(User).filter(
            User.email == payload.email).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=payload.role,
            org_id=payload.org_id,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return SignupResponse(success=True, user=UserResponse.model_validate(user))

    @router.post("/login", response_model=TokenResponse)
    def login(self, payload: LoginRequest):
        user = self.db.query(User).filter(User.email == payload.email).first()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if user.is_suspended:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account suspended",
            )
        token = create_access_token(subject=user.email)
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

    @router.post("/login/otp", response_model=TokenResponse)
    def login_otp(self, payload: OTPLoginRequest):
        # Stub – OTP verification not yet implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OTP login not yet implemented",
        )
