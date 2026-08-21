from pydantic import Field, BaseModel, ConfigDict, EmailStr, field_validator
from datetime import datetime
from typing import Annotated


class UserCreate(BaseModel):

    email: Annotated[EmailStr, Field(...)]
    password: Annotated[str, Field(..., min_length=5, max_length=30)]

    @field_validator('email', mode='after')
    @classmethod
    def check_email(cls, value: str):
        if len(value.strip()) == 0:
            raise ValueError('Incorrect email')
        return value
    
    @field_validator('password', mode='after')
    @classmethod
    def check_password(cls, value: str):
        if len(value.strip()) < 5:
            raise ValueError('Incorrect pasword')
        return value
    

class UserPatchRole(BaseModel):

    role: Annotated[str, Field(...)]

    @field_validator('role', mode='after')
    @classmethod
    def check_role(cls, value: str):
        if value not in ['customer', 'seller']:
            raise ValueError('Incorrect role')
        return value


class UserRespons(BaseModel):

    id: Annotated[int, Field()]
    email: Annotated[str, Field()]
    role: Annotated[str, Field()]
    create_at: Annotated[datetime, Field()]
    update_at: Annotated[datetime | None, Field()] = None

    model_config = ConfigDict(from_attributes=True)
        