from typing import Optional
from sqlalchemy.orm import Session
from app.accounts.models import User
from app.authentication.utils import hash_password


class AccountService:
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_id(self, db: Session, user_id) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def update_profile(self, db: Session, user: User, updates: dict) -> User:
        allowed = {"full_name", "avatar", "bio",
                   "country", "phone_number", "location"}
        for field, value in updates.items():
            if field in allowed and value is not None:
                setattr(user, field, value)
        db.commit()
        db.refresh(user)
        return user

    def create_user(self, db: Session, email: str, full_name: str, password: str, location: str, role: str = "learner", data: dict = None) -> User:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("Email already registered")

        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role=role,
            location=location,
            **(data or {}),
        )
        db.add(user)
        db.flush()
        return user
