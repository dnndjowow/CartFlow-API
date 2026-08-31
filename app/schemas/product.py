from pydantic import Field, BaseModel, ConfigDict, field_validator, model_validator
from fastapi import Form
from decimal import Decimal
from datetime import datetime
from typing import Annotated


class ProductCreate(BaseModel):
    name: Annotated[str, Field(..., max_length=100)]
    descriptions: Annotated[str | None, Field(max_length=300)] = None
    quantity: Annotated[int, Field(..., ge=0)]
    price: Annotated[Decimal, Field(..., gt=0, max_digits=12, decimal_places=2)]

    @field_validator('name', mode='after')
    @classmethod
    def check_name(cls, value: str):
        if len(value.strip()) == 0:
            raise ValueError('Incorrect name')
        return value
    
    @field_validator('descriptions', mode='after')
    @classmethod
    def check_descriptions(cls, value: str):
        if value is not None and len(value.strip()) == 0:
            raise ValueError('Incrorrect descriptions')
        return value
    
    @classmethod
    def as_form(
        cls,
        name: Annotated[str, Form(...)],
        quantity: Annotated[int, Form(...)],
        price: Annotated[Decimal, Form(...)],
        descriptions: Annotated[str | None, Form()] = None,
    ):
        return cls(
            name=name,
            descriptions=descriptions,
            quantity=quantity,
            price=price,
        )
        

class ProductUpdate(BaseModel):
    name: Annotated[str | None, Field(max_length=100)] = None
    descriptions: Annotated[str | None, Field(max_length=300)] = None
    quantity: Annotated[int | None, Field(..., ge=0)] = None
    price: Annotated[Decimal | None, Field(gt=0, max_digits=12, decimal_places=2)] = None

    @field_validator('name', 'quantity', 'price', mode='after')
    @classmethod
    def check_null(cls, value: str | int | Decimal | None):
        if value is None:
            raise ValueError('The value can not be null')
        return value
    
    @field_validator('name', mode='after')
    @classmethod
    def check_name(cls, value: str):
        if len(value.strip()) == 0:
            raise ValueError('Incorrect name')
        return value
    
    @field_validator('descriptions', mode='after')
    @classmethod
    def check_descriptions(cls, value: str):
        if value is not None and len(value.strip()) == 0:
            raise ValueError('Incrorrect descriptions')
        return value
    
    @classmethod
    def as_form(
        cls,
        name: Annotated[str | None, Form()] = None,
        descriptions: Annotated[str | None, Form()] = None,
        quantity: Annotated[int | None, Form()] = None,
        price: Annotated[Decimal | None, Form()] = None,
    ):
        
        data = {
            'name': name,
            'descriptions': descriptions,
            'quantity': quantity,
            'price': price,
        }
        
        return cls(**{
            key: value for key, value in data.items() if value is not None
        })
        

class ProductResponse(BaseModel):
    id: Annotated[int, Field()]
    seller_id: Annotated[int, Field()]
    name: Annotated[str, Field()]
    descriptions: Annotated[str | None, Field()] = None
    image_url: Annotated[str | None, Field()] = None
    quantity: Annotated[int, Field()]
    price: Annotated[Decimal, Field()]
    is_active: Annotated[bool, Field()]
    create_at: Annotated[datetime, Field()]
    update_at: Annotated[datetime | None, Field()] = None

    model_config = ConfigDict(from_attributes=True)


class ProductQuery(BaseModel):
    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1, le=100)] =20
    seller_id: Annotated[int | None, Field()] = None
    search: Annotated[str | None, Field(min_length=3, max_length=60)] = None
    in_stock: Annotated[bool | None, Field()] = None
    min_price: Annotated[Decimal | None, Field(gt=0, max_digits=12, decimal_places=2)] = None
    max_price: Annotated[Decimal | None, Field(gt=0, max_digits=12, decimal_places=2)] = None

    @model_validator(mode='after')
    def check_price(self):
        if self.max_price is not None and self.min_price is not None:
            if self.min_price > self.max_price:
                raise ValueError('Invalid price range')
        return self
    
    @field_validator('search', mode='after')
    @classmethod
    def check_search(cls, value: str | None):
        if value is None:
            raise ValueError('Incorrect search')
        if len(value.strip()) < 3:
            raise ValueError('Incorrect search')
        
        return value


class ProductList(BaseModel):
    items: Annotated[list[ProductResponse], Field()]
    total: Annotated[int, Field()]
    page: Annotated[int, Field()]
    page_size: Annotated[int, Field()]