from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from app.db_depends import get_async_db
from app.auth import decode_token
from app.models.user import User as UserModel


auth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')


async def get_current_user(
        db: Annotated[AsyncSession, Depends(get_async_db)],
        token: Annotated[str, Depends(auth2_scheme)]
):
    
    user_id = decode_token(token, 'access')

    current_user = await db.scalar(
        select(UserModel).where(
            UserModel.id == user_id,
        )
    )

    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail='Invalid token',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    return current_user


class RoleCheck:
        
    def __init__(self, role: str):
        self.role = role

    def __call__(self, current_user: Annotated[UserModel, Depends(get_current_user)]):

        if current_user.role != self.role:
            raise HTTPException(
                status_code=403,
                detail='Insufficient access rights',
            )

        return current_user