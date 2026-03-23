from typing import Any, Dict, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session


class GeneralService:

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
