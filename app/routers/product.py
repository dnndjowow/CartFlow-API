from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import Annotated
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User as UserModel
from app.schemas.product import ProductCreate, ProductList, ProductQuery, ProductResponse, ProductUpdate
from app.db_depends import get_async_db
from app.dependency import get_current_user, RoleCheck
from app.models.product import Product as ProductModel
from services.images import save_product_image , remove_product_image

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
    product: Annotated[ProductCreate, Depends(ProductCreate.as_form)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
    user: Annotated[UserModel, Depends(get_current_user)],
    image: Annotated[UploadFile | None, File()] = None,
):  
    
    image_url = None

    try:
        image_url = await save_product_image(image) if image else None
        
        new_product = ProductModel(
            **product.model_dump(),
            seller_id=user.id,
            image_url=image_url,
        )

        db.add(new_product)
        await db.commit()
    except Exception:
        await db.rollback()

        remove_product_image(image_url)

        raise


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
    product_values: Annotated[ProductUpdate, Depends(ProductUpdate.as_form)],
    image: Annotated[UploadFile | None, File()] = None,
):  
    new_image = None

    try:
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

        if product_update == {} and not image:
            raise HTTPException(
                status_code=400,
                detail='Incorrect update request'
            )


        for name, value in product_update.items():
            setattr(product_check, name, value)

        if image:
            old_image = product_check.image_url
            new_image = await save_product_image(image)
            product_check.image_url = new_image

        await db.commit()
    except Exception:
        await db.rollback()

        if new_image is not None:
            remove_product_image(new_image)

        raise
      
    if image:
        remove_product_image(old_image)

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
        .with_for_update()
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
    
    current_image = product.image_url
    product.is_active = False
    product.image_url = None

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    remove_product_image(current_image)

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
