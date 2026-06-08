from decimal import Decimal
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.general.models import AppSettings
from app.settings import APP_NAME


DEFAULT_APP_SETTINGS: Dict[str, Any] = {
    "app_name": APP_NAME,
    "logo": None,
    "contacts": None,
    "email": None,
    "iq_test_price": Decimal("299.0"),
    "refresh_booking_in_minute": 5,
    "psychologist_booking_reminder_in_minutes": 30,
}


class GeneralService:
    def app_settings_table_exists(self, db: Session) -> bool:
        bind = db.get_bind()
        if bind is None:
            return False
        return inspect(bind).has_table(AppSettings.__tablename__)

    def get_app_settings(self, db: Session) -> AppSettings:
        settings = db.query(AppSettings).order_by(AppSettings.created_at.asc()).first()
        if settings:
            return settings

        settings = AppSettings(**DEFAULT_APP_SETTINGS)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings

    def update_app_settings(self, db: Session, updates: Dict[str, Any]) -> AppSettings:
        settings = self.get_app_settings(db=db)
        for field, value in updates.items():
            if value is None:
                continue
            if field == "iq_test_price":
                value = Decimal(str(value))
            if field == "refresh_booking_in_minute":
                value = int(value)
            if field == "psychologist_booking_reminder_in_minutes":
                value = int(value)
            setattr(settings, field, value)
        db.commit()
        db.refresh(settings)
        return settings

    def seed_app_settings(self, db: Session) -> Optional[AppSettings]:
        if not self.app_settings_table_exists(db=db):
            return None
        return self.get_app_settings(db=db)

    def create(self, db: Session, data: Dict[str, Any], model: Type) -> Any:
        instance = model(**data)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    def get(self, db: Session, key: Any, model: Type) -> Optional[Any]:
        return db.query(model).filter(model.id == key).first()

    def list_data(self, db: Session, model: Type) -> List[Any]:
        return db.query(model).all()

    def filter_data(
        self, db: Session, model: Type, filters: Dict[str, Any]
    ) -> List[Any]:
        query = db.query(model)
        for attr, value in filters.items():
            query = query.filter(getattr(model, attr) == value)
        return query.all()

    def update_data(
        self, db: Session, key: Any, data: Dict[str, Any], model: Type
    ) -> Optional[Any]:
        instance = db.query(model).filter(model.id == key).first()
        if not instance:
            return None
        for field, value in data.items():
            setattr(instance, field, value)
        db.commit()
        db.refresh(instance)
        return instance

    def delete(self, db: Session, key: Any, model: Type) -> bool:
        instance = db.query(model).filter(model.id == key).first()
        if not instance:
            return False
        db.delete(instance)
        db.commit()
        return True
