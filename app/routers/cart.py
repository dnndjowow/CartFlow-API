from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.models.user import User as UserModel
from app.schemas.cart import CreateItemsCart, UpdateCartQuantity, ItemsCartResponse
from app.db_depends import get_async_db
from app.dependency import get_current_user
from app.models.cart import Cart as CartModel
from app.models.cartitem import CartItem as CartItemModel
from app.models.product import Product as ProductModel

router = APIRouter(
    prefix='/cart',
    tags=['cart'],
)


@router.get('/', response_model=list[ItemsCartResponse])
async def get_cart_items(
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    cart_item = (await db.scalars(
        select(CartItemModel)
        .join(CartModel, CartItemModel.cart_id == CartModel.id)
        .where(
            CartModel.user_id == user.id
        )
        .options(selectinload(CartItemModel.product))
    )
).all()
    
    return cart_item


@router.post('/', response_model=ItemsCartResponse, status_code=status.HTTP_200_OK)
async def add_rpoduct_in_cart(
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
    item: CreateItemsCart,
):
    
    cart = await db.scalar(
        select(CartModel).where(
            CartModel.user_id == user.id
        )
        .with_for_update()
    )

    if cart is None:
        raise HTTPException(
            status_code=404,
            detail='Cart is not found',
        )

    product_check = await db.scalar(
        select(ProductModel).where(
            ProductModel.id == item.product_id,
            ProductModel.is_active.is_(True),
        )
    )
    
    if product_check is None:
        raise HTTPException(
            status_code=404,
            detail='Product is not found',
        )
    
    order_item_check = await db.scalar(
        select(CartItemModel).where(
            CartItemModel.product_id == item.product_id,
            CartItemModel.cart_id == cart.id,
        )
    )
    
    if order_item_check is not None:

        if product_check.quantity < (item.quantity+order_item_check.quantity):
            raise HTTPException(
                status_code=400,
                detail='This quantity of the product is not in stock',
            )
        
        quantity = item.quantity+order_item_check.quantity
        price = Decimal(str(quantity*product_check.price))

        if price > Decimal("9999999999.99"):
            raise HTTPException(
                status_code=400,
                detail="Total price is too large",
            )

        order_item_check.quantity = quantity
        new_cart_item = order_item_check
    
    else:

        if product_check.quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail='This quantity of the product is not in stock',
            )
        
        quantity = item.quantity
        price = Decimal(str(quantity*product_check.price))

        if price > Decimal("9999999999.99"):
            raise HTTPException(
                status_code=400,
                detail="Total price is too large",
            )

        
        new_cart_item = CartItemModel(
            cart_id=cart.id,
            product_id=item.product_id,
            quantity=quantity,
            product=product_check
        )

        db.add(new_cart_item)

    await db.commit()
    await db.refresh(
        new_cart_item,
        attribute_names=["product"],
    )

    return new_cart_item


@router.patch('/items/{cart_item_id}', response_model=ItemsCartResponse)
async def update_quantity(
    cart_item_id: int,
    item: UpdateCartQuantity,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):  
    
    cart_item = await db.scalar(
        select(CartItemModel)
        .join(CartModel, CartItemModel.cart_id == CartModel.id)
        .join(ProductModel, CartItemModel.product_id == ProductModel.id)
        .where(
            CartModel.user_id == user.id,
            CartItemModel.id == cart_item_id,
            ProductModel.is_active.is_(True),
        )
        .options(selectinload(CartItemModel.product))
        .with_for_update()
    )

    if cart_item is None:
        raise HTTPException(
            status_code=404,
            detail='Item is not found or product is inactive',
        )

    product = cart_item.product
    
    if product.quantity < item.quantity:
        raise HTTPException(
            status_code=400,
            detail='This quantity of the product is not in stock',
        )

    cart_item.quantity = item.quantity
    price = item.quantity * product.price

    if price > Decimal("9999999999.99"):
        raise HTTPException(
            status_code=400,
            detail="Total price is too large",
        )

    await db.commit()
    await db.refresh(cart_item)

    return cart_item


@router.delete('/items/{cart_item_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    cart_item_id: int,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    item_check = await db.scalar(
        select(CartItemModel)
        .join(CartModel, CartItemModel.cart_id == CartModel.id)
        .where(
            CartItemModel.id == cart_item_id,
            CartModel.user_id == user.id,
        )
        .with_for_update()
    )

    if item_check is None:
        raise HTTPException(
            status_code=404,
            detail='Item is not found',
        )

    await db.delete(item_check)
    await db.commit()

    return None


@router.delete('/items', status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_items(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    user: Annotated[UserModel, Depends(get_current_user)],
):
    
    cart = await db.scalar(
        select(CartModel).where(
            CartModel.user_id == user.id
        )
        .with_for_update()
    )

    if cart is None:
        raise HTTPException(
            status_code=404,
            detail="Cart not found",
        )

    await db.execute(
        delete(CartItemModel).where(
            CartItemModel.cart_id == cart.id
        )
    )

    await db.commit()

    return None