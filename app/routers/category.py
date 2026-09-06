from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


from app.models.category import Category as CategoryModel
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.db_depends import get_async_db
from app.dependency import RoleCheck
from app.models.product import Product as ProductModel


router = APIRouter(
    prefix='/categories',
    tags=['categories']
)

@router.get('/{category_id}', response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    get_category = await db.scalar(
        select(CategoryModel).where(
            CategoryModel.id == category_id,
            CategoryModel.is_active.is_(True),
        )
    )

    if get_category is None:
        raise HTTPException(
            status_code=404,
            detail='Category is not found',
        )
    
    return get_category


@router.get('/', response_model=list[CategoryResponse])
async def get_categories(
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    stmt = select(CategoryModel).where(
        CategoryModel.is_active.is_(True),
    )

    categories = await db.scalars(stmt)

    return categories.all()


@router.post(
    '/',
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleCheck(['admin']))],
)
async def create_category(
    category: CategoryCreate,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    if category.parent_id is not None:

        parent_category = await db.scalar(
            select(CategoryModel)
            .where(
                CategoryModel.id == category.parent_id,
                CategoryModel.is_active.is_(True),
            )
            .with_for_update(read=True)
        )

        if parent_category is None:
            raise HTTPException(
                status_code=400,
                detail='Category is not Found',
            )
        
    new_category = CategoryModel(
        **category.model_dump()
    )

    db.add(new_category)

    try:
        await db.commit()
        await db.refresh(new_category)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail='A category with this name already exists'
        )
    
    return new_category


@router.patch(
    '/{category_id}',
    response_model=CategoryResponse,
    dependencies=[Depends(RoleCheck(['admin']))],
)
async def update_category(
    category_id: int,
    category: CategoryUpdate,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):

    get_category = await db.scalar(
        select(CategoryModel)
        .where(
            CategoryModel.id == category_id,
            CategoryModel.is_active.is_(True),
        )
        .with_for_update()
    )

    if get_category is None:
        raise HTTPException(
            status_code=404,
            detail='category is not found',
        )
    
    new_category = category.model_dump(exclude_unset=True)

    if not new_category:
        raise HTTPException(
            status_code=400,
            detail='Category can not be none',
        )
    
    try:

        if 'parent_id' in new_category and new_category.get('parent_id') is not None:

            get_new_parrent = await db.scalar(
                select(CategoryModel)
                .where(
                    CategoryModel.id == new_category.get('parent_id'),
                    CategoryModel.is_active.is_(True),
                )
                .with_for_update(read=True)
            ) 

            if get_new_parrent is None:
                raise HTTPException(
                    status_code=404,
                    detail='Category is not found',
                )
            
            if get_new_parrent.id == get_category.id:
                raise HTTPException(
                    status_code=400,
                    detail='The current category cannot be its own parent',
                )
            
            new_parent_id = new_category.get('parent_id')

            while new_parent_id is not None:

                cur_category = await db.scalar(
                    select(CategoryModel)
                    .where(
                        CategoryModel.id == new_parent_id,
                        CategoryModel.is_active.is_(True),
                    )
                    .with_for_update(read=True)
                )

                if not cur_category:
                    break

                if cur_category.id == get_category.id:
                    raise HTTPException(
                        status_code=400,
                        detail='You cannot assign its descendant as the new parent',
                    )
                
                new_parent_id = cur_category.parent_id


        for key, value in new_category.items():
            setattr(get_category, key, value)

        await db.commit()
        await db.refresh(get_category)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail='Category with this name already exists under the specified parent'
        )
        
    return get_category


@router.delete(
    '/{category_id}',
    response_model=CategoryResponse,
    dependencies=[Depends(RoleCheck(['admin']))],
)
async def delete_category(
    category_id: int,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    get_category = await db.scalar(
        select(CategoryModel)
        .where(
            CategoryModel.id == category_id,
            CategoryModel.is_active.is_(True),
        )
        .options(selectinload(CategoryModel.products))
        .with_for_update()
    )

    if get_category is None:
        raise HTTPException(
            status_code=404,
            detail='category is not found',
        )
    
    for product in get_category.products:

        if product.is_active == True:

            raise HTTPException(
                status_code=400,
                detail='Category have active products',
            )
        
    child_category = await db.scalars(
        select(CategoryModel)
        .where(
            CategoryModel.parent_id == get_category.id,
            CategoryModel.is_active == True,
        )
        .with_for_update(read=True)
    )
    
    if len(child_category.all()) != 0:
        raise HTTPException(
            status_code=400,
            detail='You cannot delete category with active child categories',
        )
    
    try:

        get_category.is_active = False

        await db.commit()
        await db.refresh(get_category)

    except Exception:
        await db.rollback()
        raise

    return get_category


    
    
    
    



