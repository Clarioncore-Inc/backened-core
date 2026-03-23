from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.accounts.models import User
from app.courses.models import Course
from app.enrollments.models import Enrollment
from app.payments.models import Payment

# In-memory settings store (replace with DB-backed model if needed)
_platform_settings: Dict[str, Any] = {
    "platform_name": "CerebroLearn",
    "maintenance_mode": False,
    "allow_signups": True,
    "default_currency": "USD",
    "platform_fee_rate": 0.20,
}


class AdminService:
    def get_all_users(self, db: Session) -> List[User]:
        return db.query(User).all()

    def get_all_courses(self, db: Session) -> List[Course]:
        return db.query(Course).all()

    def get_analytics(self, db: Session) -> Dict[str, Any]:
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_courses = db.query(func.count(Course.id)).scalar() or 0
        total_enrollments = db.query(func.count(Enrollment.id)).scalar() or 0
        total_revenue = (
            db.query(func.sum(Payment.amount))
            .filter(Payment.status == "completed")
            .scalar()
            or 0
        )
        return {
            "total_users": total_users,
            "total_courses": total_courses,
            "total_enrollments": total_enrollments,
            "total_revenue": float(total_revenue),
        }

    def update_user_role(self, db: Session, user_id, role: str) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.role = role
            db.commit()
            db.refresh(user)
        return user

    def update_user_status(self, db: Session, user_id, suspended: bool) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_suspended = suspended
            db.commit()
            db.refresh(user)
        return user

    def get_settings(self) -> Dict[str, Any]:
        return dict(_platform_settings)

    def update_settings(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        _platform_settings.update({k: v for k, v in updates.items() if v is not None})
        return dict(_platform_settings)

