from typing import Optional
from sqlalchemy.orm import Session
from app.accounts.models import User


class AccountService:
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_id(self, db: Session, user_id) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def update_profile(self, db: Session, user: User, updates: dict) -> User:
        allowed = {"full_name", "avatar", "bio", "country", "phone_number"}
        for field, value in updates.items():
            if field in allowed and value is not None:
                setattr(user, field, value)
        db.commit()
        db.refresh(user)
        return user

