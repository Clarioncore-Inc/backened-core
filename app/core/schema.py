from pydantic import BaseModel as PydanticBase


class BaseSchema(PydanticBase):
    model_config = {"from_attributes": True, "populate_by_name": True}

