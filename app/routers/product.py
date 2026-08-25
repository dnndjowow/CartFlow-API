from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User as UserModel
from app.schemas.product import ProductCreate, ProductList, ProductQuery, ProductResponse, ProductUpdate
from app.db_depends import get_async_db
from app.dependency import get_current_user, RoleCheck
from app.models.product import Product as ProductModel

router = APIRouter(
    prefix='/products',
    tags=['product'],
)

@router.post(
    '/',
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleCheck(['seller']))]
)
async def create_product(
    product: ProductCreate,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    user: Annotated[UserModel, Depends(get_current_user)],
):
    
    new_product = ProductModel(
        **product.model_dump(),
        seller_id=user.id,
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    return new_product


@router.patch(
    '/{product_id}',
    response_model=ProductResponse,
    dependencies=[Depends(RoleCheck(['seller']))]
)
async def update_product(
    product_id: int,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    user: Annotated[UserModel, Depends(get_current_user)],
    product_values: ProductUpdate,
):
    
    product_check = await db.scalar(
        select(ProductModel).where(
            ProductModel.id == product_id,
            ProductModel.is_active.is_(True)
        )
        .with_for_update()
    )

    if product_check is None:
        raise HTTPException(
            status_code=404,
            detail='Product is not found'
        )
    
    if product_check.seller_id != user.id:
        raise HTTPException(
            status_code=403,
            detail='Seller can not update not mine product',
        )
    
    product_update = product_values.model_dump(exclude_unset=True)

    if product_update == {}:
        raise HTTPException(
            status_code=400,
            detail='Incorrect update request'
        )

    for name, value in product_update.items():
        setattr(product_check, name, value)

    await db.commit()
    await db.refresh(product_check)

    return product_check


@router.delete(
    '/{product_id}',
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleCheck(['seller', 'admin']))]
)
async def delete_product(
    product_id: int,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    
    product = await db.scalar(
        select(ProductModel).where(
            ProductModel.id == product_id,
            ProductModel.is_active.is_(True),
        )
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail='Active product is nor found',
        )
    
    if current_user.role != 'admin' and product.seller_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail='Seller can not delete not mine product',
        )

    product.is_active = False

    await db.commit()
    await db.refresh(product)

    return product


@router.get('/{product_id}', response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    product = await db.scalar(
        select(ProductModel).where(
            ProductModel.id == product_id,
            ProductModel.is_active.is_(True),
        )
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail='Active product is not found',
        )
    
    return product


@router.get('/', response_model=ProductList)
async def get_products(
    parametrs: Annotated[ProductQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    filters = [ProductModel.is_active.is_(True)]

    if parametrs.seller_id is not None:
        filters.append(ProductModel.seller_id == parametrs.seller_id)

    if parametrs.in_stock is not None:
        filters.append(ProductModel.quantity != 0 if parametrs.in_stock == True else ProductModel.quantity == 0)

    if parametrs.min_price is not None:
        filters.append(ProductModel.price >= parametrs.min_price)

    if parametrs.max_price is not None:
        filters.append(ProductModel.price <= parametrs.max_price)

    rank_col = None

    if parametrs.search is not None:
        search_value = parametrs.search.strip()

        if search_value:

            ts_query = func.websearch_to_tsquery('english', search_value)
            filters.append(ProductModel.tsv.op('@@')(ts_query))
            rank_col = func.ts_rank_cd(ProductModel.tsv, ts_query).label('rank')

    if rank_col is not None:

        items = (await db.scalars(
            select(ProductModel, rank_col)
            .where(*filters)
            .order_by(rank_col.desc(), ProductModel.id)
            .offset((parametrs.page - 1) * parametrs.page_size)
            .limit(parametrs.page_size)
        )
    ).all()
    
    else:
        items = (await db.scalars(
            select(ProductModel)
            .where(*filters)
            .order_by(ProductModel.id)
            .offset((parametrs.page - 1) * parametrs.page_size)
            .limit(parametrs.page_size)
        )
    ).all()

    total = await db.scalar(
        select(func.count())
        .select_from(ProductModel)
        .where(*filters)
    )

    return {
        'items': items,
        'total': total,
        'page': parametrs.page,
        'page_size': parametrs.page_size,
    }
