from pydantic import Field, BaseModel, ConfigDict, field_validator
from decimal import Decimal
from datetime import datetime
from typing import Annotated


class OrderStatusUpdate(BaseModel):
    status: str

    @field_validator('status', mode='after')
    @classmethod
    def update_status(cls, value: str):
        if value not in ['paid', 'cancelled', 'completed']:
            raise ValueError('Incrorrect status')
        return value
    

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    price: Decimal
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)