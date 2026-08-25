from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.models.user import User as UserModel
from app.models.cart import Cart as CartModel
from app.schemas.order import OrderResponse, OrderStatusUpdate, OrderList, OrderQuery
from app.db_depends import get_async_db
from app.dependency import get_current_user, RoleCheck
from app.models.order import Order as OrderModel
from app.models.orderitem import OrderItem as OrderItemModel
from app.models.cartitem import CartItem as CartItemModel
from app.models.product import Product as ProductModel


router = APIRouter(
    prefix='/order',
    tags=['order'],
)

@router.post('/', response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)]
):
    
    try:
        
        cart = await db.scalar(
            select(CartModel)
            .where(CartModel.user_id == user.id)
            .options(selectinload(CartModel.cart_items))
            .with_for_update()
        )

        if cart is None:
            raise HTTPException(
                status_code=404,
                detail='Cart is not found',
            )
        
        if len(cart.cart_items) == 0:
            raise HTTPException(
                status_code=400,
                detail='The cart is empty',
            )
        
        cart_items = sorted(cart.cart_items, key=lambda parametrs: parametrs.product_id)
        order_items_list = []

        total_price = Decimal('0.00')


        new_order = OrderModel(
            user_id=user.id,
            price=total_price,
        )

        db.add(new_order)
        await db.flush()
    
        for cart_item in cart_items:

            product_check = await db.scalar(
                select(ProductModel)
                .where(
                    ProductModel.id == cart_item.product_id,
                    ProductModel.is_active.is_(True),
                )
                .with_for_update()
            )
            
            if product_check is None:
                raise HTTPException(
                    status_code=404,
                    detail='Product is not found'
                )

            if product_check.quantity < cart_item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail='This quantity of the item is not in stock'
                )
            
            price = cart_item.quantity * product_check.price

            if price > Decimal("9999999999.99"):
                raise HTTPException(
                    status_code=400,
                    detail="Total price is too large",
                )
            
            total_price += price

            if total_price > Decimal("9999999999.99"):
                raise HTTPException(
                    status_code=400,
                    detail="Total price is too large",
                )
        
            product_check.quantity -= cart_item.quantity

            order_item = OrderItemModel(
                order_id=new_order.id,
                product_id=product_check.id,
                quantity=cart_item.quantity,
                price=price,
            )

            db.add(order_item)

            order_items_list.append(order_item)
        
        new_order.price = total_price

        await db.execute(
            delete(CartItemModel).where(
                CartItemModel.cart_id == cart.id
            )
        )

        await db.commit()

    except Exception:
        await db.rollback()
        raise 

    return {
        "id": new_order.id,
        "user_id": new_order.user_id,
        "status": new_order.status,
        "price": new_order.price,
        "items": order_items_list,
    }


@router.get('/orderlist', response_model=list[OrderResponse])
async def get_orders(
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):

    orders = await db.scalars(
        select(OrderModel).where(OrderModel.user_id == user.id,)
        .options(selectinload(OrderModel.items))
    )

    result = []

    for order in orders.all():
        
        result.append(
            {
                'id': order.id,
                'user_id': order.user_id,
                'status': order.status,
                'price': order.price,
                'items': order.items,
            }
        )

    return result


@router.get(
    '/orderlist/admin',
    response_model=OrderList,
    dependencies=[Depends(RoleCheck(['admin']))]
)
async def get_order_admin(
    parametrs: Annotated[OrderQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    filters = []

    if parametrs.order_id is not None:
        filters.append(OrderModel.id == parametrs.order_id)

    if parametrs.status is not None:
        filters.append(OrderModel.status == parametrs.status)

    if parametrs.create_with is not None:
        filters.append(OrderModel.create_at >= parametrs.create_with)

    if parametrs.create_up is not None:
        filters.append(OrderModel.create_at <= parametrs.create_up)

    if parametrs.min_price is not None:
        filters.append(OrderModel.price >= parametrs.min_price)

    if parametrs.max_price is not None:
        filters.append(OrderModel.price <= parametrs.max_price)


    total = await db.scalar(
        select(func.count())
        .select_from(OrderModel)
        .where(*filters)
    )

    items = await db.scalars(
        select(OrderModel)
        .where(*filters)
        .order_by(OrderModel.id)
        .offset((parametrs.page - 1) * parametrs.page_size)
        .limit(parametrs.page_size)
        .options(selectinload(OrderModel.items))
    )

    return {
        'items': items.all(),
        'total': total,
        'page': parametrs.page,
        'page_size': parametrs.page_size,
    }

@router.get('/{order_id}', response_model=OrderResponse)
async def get_order(
    order_id: int,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    order = await db.scalar(
        select(OrderModel).where(
            OrderModel.user_id == user.id,
            OrderModel.id == order_id,
        )
        .options(selectinload(OrderModel.items))
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail='Order is not found',
        )
    
    return {
        "id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "price": order.price,
        "items": order.items,
    }


@router.patch(
    '/{order_id}',
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleCheck(['admin', 'customer']))]
)
async def update_status(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    new_status: OrderStatusUpdate,
    user: Annotated[UserModel, Depends(get_current_user)],
):  
    
    if user.role == 'admin':
    
        order = await db.scalar(
            select(OrderModel)
            .where(
                OrderModel.id == order_id,
            )
            .options(selectinload(OrderModel.items))
            .with_for_update()
        )

    else:
        order = await db.scalar(
            select(OrderModel)
            .where(
                OrderModel.id == order_id,
                OrderModel.user_id == user.id
            )
            .options(selectinload(OrderModel.items))
            .with_for_update()
        )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail='Order is nor found',
        )
    
    if order.status in ['completed', 'cancelled']:
        raise HTTPException(
            status_code=400,
            detail='This status is final',
        )
    
    table_transfer = {
        'pending': ['paid', 'cancelled'],
        'paid': ['completed'],
    }

    if user.role == 'customer' and new_status.status != 'cancelled':
        raise HTTPException(
            status_code=403,
            detail='Customer can only cancelled order'
        )

    if new_status.status not in table_transfer.get(order.status):
        raise HTTPException(
            status_code=400,
            detail='Incorrect status transfer',
        )
    
    
    sort_order_item = sorted(order.items, key=lambda parametr: parametr.product_id)

    
    if new_status.status == 'cancelled':

        for item in sort_order_item:

            product = await db.scalar(
                select(ProductModel)
                .where(
                    ProductModel.id == item.product_id,
                )
                .with_for_update()
            )

            product.quantity += item.quantity

    order.status = new_status.status

    await db.commit()

    return {
        "id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "price": order.price,
        "items": order.items,
    }




        


    



