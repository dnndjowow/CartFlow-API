from pydantic import Field, BaseModel, ConfigDict, field_validator, model_validator, AwareDatetime
from decimal import Decimal
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


class OrderList(BaseModel):
    items: Annotated[list[OrderResponse], Field()]
    total: Annotated[int, Field()]
    page: Annotated[int, Field()]
    page_size: Annotated[int, Field()]


class OrderQuery(BaseModel):
    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1, le=100)] =20
    order_id: Annotated[int | None, Field(ge=1)] = None
    status: Annotated[str | None, Field()] = None
    create_with: AwareDatetime | None = None
    create_up: AwareDatetime | None = None
    min_price: Annotated[Decimal | None, Field(gt=0, max_digits=12, decimal_places=2)] = None
    max_price: Annotated[Decimal | None, Field(gt=0, max_digits=12, decimal_places=2)] = None

    @model_validator(mode='after')
    def check_price(self):
        if self.max_price is not None and self.min_price is not None:
            if self.min_price > self.max_price:
                raise ValueError('Invalid price range')
        return self
    
    @model_validator(mode='after')
    def check_date(self):
        if self.create_up is not None and self.create_with is not None:
            if self.create_up < self.create_with:
                raise ValueError('Invalid dates range')
        return self

    @field_validator('status', mode='after')
    @classmethod
    def update_status(cls, value: str):
        if value is not None:
            if value not in ['pending', 'paid', 'cancelled', 'completed']:
                raise ValueError('Incrorrect status')
        return value
    
