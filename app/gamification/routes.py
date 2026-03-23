from typing import List

from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from app.accounts.models import User
from app.accounts.schemas import UserPublic
from app.dependencies import get_db

router = APIRouter(prefix="/leaderboard", tags=["gamification"])


@cbv(router)
class LeaderboardView:
    db: Session = Depends(get_db)

    @router.get("/", response_model=List[UserPublic])
    def get_leaderboard(self):
        return (
            self.db.query(User)
            .filter(User.is_active == True, User.is_suspended == False)
            .order_by(User.xp.desc())
            .limit(100)
            .all()
        )
