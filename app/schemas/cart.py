from pydantic import Field, BaseModel, ConfigDict, field_validator
from decimal import Decimal
from datetime import datetime
from typing import Annotated


class CreateItemsCart(BaseModel):
    product_id: Annotated[int, Field(..., ge=1)]
    quantity: Annotated[int, Field(..., ge=1)]


class UpdateCartQuantity(BaseModel):
    quantity: Annotated[int, Field(..., ge=1)]


class ItemsCartResponse(BaseModel):
    id: Annotated[int, Field()]
    cart_id: Annotated[int, Field()]
    product_id: Annotated[int, Field()]
    quantity: Annotated[int, Field()]
    price: Annotated[Decimal, Field()]

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: Annotated[int, Field()]
    cart_items: Annotated[list[ItemsCartResponse], Field()]
    user_id: Annotated[int, Field()]
    create_at: Annotated[datetime, Field()]
    update_at: Annotated[datetime | None, Field()] = None

    model_config = ConfigDict(from_attributes=True)