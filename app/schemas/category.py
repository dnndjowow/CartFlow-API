from pydantic import Field, BaseModel, field_validator, model_validator, ConfigDict
from typing import Annotated
from datetime import datetime


class CategoryCreate(BaseModel):
    parent_id: Annotated[int | None, Field(gt=0)] = None
    name: Annotated[str, Field(..., max_length=50)]

    @field_validator('name', mode='after')
    @classmethod
    def check_name(cls, value: str):
        if len(value.strip()) == 0:
            raise ValueError('Incorrect name')
        
        return value
    

class CategoryUpdate(BaseModel):
    parent_id: Annotated[int | None, Field(gt=0)] = None
    name: Annotated[str | None, Field(max_length=50)] = None

    @field_validator('name', mode='after')
    @classmethod
    def check_name(cls, value: str | None):
        if value is None:
            raise ValueError('Incorrect name')
        if len(value.strip()) == 0:
            raise ValueError('Incorrect name')
        
        return value
    

class CategoryResponse(BaseModel):
    id: Annotated[int, Field()]
    parent_id: Annotated[int | None, Field()]
    name: Annotated[str, Field()]
    is_active: Annotated[bool, Field()]
    create_at: Annotated[datetime, Field()]
    update_at: Annotated[datetime | None, Field()]

    model_config = ConfigDict(from_attributes=True)