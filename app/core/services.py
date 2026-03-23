"""
Abstract interface documentation for GeneralService.
The concrete implementation lives in app.general.service.
"""
from typing import Any, Dict, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class AbstractGeneralService:
    """Describes the contract that GeneralService must fulfil."""

    def create(self, db: Session, data: Dict[str, Any], model: Type) -> Any:
        raise NotImplementedError

    def get(self, db: Session, key: Any, model: Type) -> Optional[Any]:
        raise NotImplementedError

    def list_data(self, db: Session, model: Type) -> List[Any]:
        raise NotImplementedError

    def filter_data(
        self, db: Session, model: Type, filters: Dict[str, Any]
    ) -> List[Any]:
        raise NotImplementedError

    def update_data(
        self, db: Session, key: Any, data: Dict[str, Any], model: Type
    ) -> Optional[Any]:
        raise NotImplementedError

    def delete(self, db: Session, key: Any, model: Type) -> bool:
        raise NotImplementedError

