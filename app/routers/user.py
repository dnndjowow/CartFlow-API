from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError

from app.models.user import User as UserModel
from app.schemas.user import UserRespons, UserPatchRole, UserCreate
from app.db_depends import get_async_db
from app.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.schemas.auth import TokenResponse, AccessTokenResponse, RefreshToken
from app.dependency import get_current_user, RoleCheck
from app.models.product import Product as ProductModel
from app.models.order import Order as OrderModel
from app.models.cart import Cart as CartModel


router = APIRouter(
    tags=['user']
)


@router.post('/registr', response_model=UserRespons, status_code=status.HTTP_201_CREATED)
async def registr_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):

    try:  
        email_check = await db.scalar(
            select(UserModel).where(
                UserModel.email == user.email,
            )
        )

        if email_check is not None:
            raise HTTPException(
                status_code=409,
                detail='This email is already in use',
            )
        
        new_user = UserModel(
            email=user.email,
            hashed_password=hash_password(user.password),
        )

        db.add(new_user)
        await db.flush()

        new_cart = CartModel(
            user_id=new_user.id,
        )

        db.add(new_cart)
        await db.commit()

    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )
    
    except Exception:
        await db.rollback()
        raise

    return new_user


@router.post('/auth/token', response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def create_token(
    user_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):

    user_check = await db.scalar(
        select(UserModel).where(
            UserModel.email == user_data.username,
        )
    )

    if user_check is None:
        raise HTTPException(
            status_code=401,
            detail='Email or password incorrect',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    if not verify_password(user_data.password, user_check.hashed_password):
        raise HTTPException(
            status_code=401,
            detail='Email or password incorrect',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    access_token = create_access_token(data={'sub': str(user_check.id)})
    refresh_token = create_refresh_token(data={'sub': str(user_check.id)})

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer',
    }


@router.post('/token/access', response_model=AccessTokenResponse, status_code=status.HTTP_200_OK)
async def creare_new_access_token(
    token: RefreshToken,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    payload_user_id = decode_token(token.refresh_token, 'refresh')

    user = await db.scalar(
        select(UserModel).where(
            UserModel.id == payload_user_id,
        )
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail='Email or password incorrect',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    new_token = create_access_token(data={'sub': str(user.id)})

    return {
        'access_token': new_token,
        'token_type': 'bearer',
    }


@router.get('/me', response_model=UserRespons)
async def get_user(
    user: Annotated[UserModel, Depends(get_current_user)],
):
    
    return user


@router.patch(
    '/user/role/{user_id}',
    response_model=UserRespons,
    dependencies=[Depends(RoleCheck(['admin']))]
)
async def update_user_role(
    user_id: int,
    user: UserPatchRole,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    user_check = await db.scalar(
        select(UserModel).where(
            UserModel.id == user_id,
        )
    )

    if user_check is None:
        raise HTTPException(
            status_code=404,
            detail='User is not found',
        )
    
    if user_check.role == user.role:
        raise HTTPException(
            status_code=400,
            detail='You cannot change the role to the same one',
        )
    
    if user.role == 'customer':
        
        product_check = await db.scalar(
            select(ProductModel).where(
                ProductModel.seller_id == user_check.id,
            )
        )

        if product_check is not None:
            raise HTTPException(
                status_code=400,
                detail='You cannot change the role if the seller has products'
            )
        
    if user.role == 'seller':

        order_check = await db.scalar(
            select(OrderModel).where(
                OrderModel.user_id == user_id,
                OrderModel.status.in_(['pending', 'paid']),
            )
        )

        if order_check is not None:
            raise HTTPException(
                status_code=400,
                detail='The seller role cannot be changed if there are incomplete orders'
            )
        
    user_check.role = user.role

    await db.commit()
    await db.refresh(user_check)

    return user_check
    

@router.delete('/user/delete/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    curr_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    
    if user_id != curr_user.id and curr_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="User cannot delete another user's",
        )
    
    user_check = await db.scalar(
        select(UserModel).where(
            UserModel.id == user_id,
        )
    )

    if user_check is None:
        raise HTTPException(
            status_code=404,
            detail='User is not found',
        )


    product_check = await db.scalar(
        select(ProductModel).where(
            ProductModel.seller_id == user_id,
        )
    )

    if product_check is not None:
        raise HTTPException(
            status_code=400,
            detail='A seller account cannot be deleted while there are active products',
        )


    order_check = await db.scalar(
        select(OrderModel).where(
            OrderModel.user_id == user_id,
        )
    )

    if order_check is not None:
        raise HTTPException(
            status_code=400,
            detail='A customer account cannot be deleted if there are active orders',
        )
            
    await db.delete(user_check)
    await db.commit()

    return None

