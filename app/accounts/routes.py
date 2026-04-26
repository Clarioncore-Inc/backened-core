from app import settings
from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User
from app.accounts.schemas import UserResponse, UserUpdate, SetPasswordSchema
from app.core.dependency_injection import service_locator

router = APIRouter(prefix="/accounts", tags=["accounts"])

public_router = APIRouter(prefix="/accounts", tags=["accounts"])


signer = URLSafeTimedSerializer(settings.SECRET_KEY)


@cbv(router)
class AccountsView:
    current_user: User = Depends(get_current_active_user)
    db: Session = Depends(get_db)

    @router.get("/profile", response_model=UserResponse)
    def get_profile(self):
        return self.current_user

    @router.put("/profile", response_model=UserResponse)
    def update_profile(self, updates: UserUpdate):
        return service_locator.account_service.update_profile(
            db=self.db,
            user=self.current_user,
            updates=updates.model_dump(exclude_unset=True),
        )


@cbv(public_router)
class PublicAccountsView:
    db: Session = Depends(get_db)

    @public_router.post("/set-password", response_model=UserResponse)
    def set_password(self, payload: SetPasswordSchema):
        try:
            user_id = signer.loads(
                payload.token, max_age=settings.COLLABORATOR_INVITE_TOKEN_EXPIRY)
        except SignatureExpired:
            raise HTTPException(status_code=400, detail="Token has expired")
        except BadSignature:
            raise HTTPException(status_code=400, detail="Invalid token")

        return service_locator.account_service.set_password(
            db=self.db,
            user_id=user_id,
            data=payload.model_dump(exclude={"token"}, exclude_unset=True),
        )
