from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.authentication.utils import get_current_active_user
from app.accounts.models import User
from app.accounts.schemas import UserResponse, UserUpdate
from app.core.dependency_injection import service_locator

router = APIRouter(prefix="/accounts", tags=["accounts"])


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

