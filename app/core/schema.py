from pydantic import BaseModel as PydanticBase, model_validator
from typing import Any, get_args, get_origin, Union
import uuid


class BaseSchema(PydanticBase):
    model_config = {
        "from_attributes": True, "populate_by_name": True
    }

    @model_validator(mode="before")
    @classmethod
    def normalize_empty_uuid_values(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)

        for field_name, field_info in cls.model_fields.items():
            annotation = field_info.annotation
            origin = get_origin(annotation)
            args = get_args(annotation)

            is_uuid = annotation is uuid.UUID or (
                origin is Union and uuid.UUID in args)
            is_uuid_list = (
                origin is list and args and args[0] is uuid.UUID
            ) or (
                origin is Union and any(
                    get_origin(a) is list and get_args(
                        a) and get_args(a)[0] is uuid.UUID
                    for a in args
                )
            )

            value = normalized.get(field_name)

            if is_uuid and isinstance(value, str) and not value.strip():
                normalized[field_name] = None
            elif is_uuid_list:
                if isinstance(value, str) and not value.strip():
                    normalized[field_name] = None
                elif isinstance(value, list):
                    normalized[field_name] = [
                        item for item in value
                        if not (isinstance(item, str) and not item.strip())
                    ]

        return normalized
