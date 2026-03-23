from pydantic import BaseModel as PydanticBase


class BaseSchema(PydanticBase):
    model_config = {"from_attributes": True}

