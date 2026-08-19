from pwdlib import PasswordHash
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
import jwt

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, REFRESH_TOKEN_EXPIRE_DAYS, SECRET_KEY


password_hash = PasswordHash.recommended()


def hash_password(password: str):
    return password_hash.hash(password)


def verify_password(plain_password: str, cur_password: str):
    return password_hash.verify(plain_password, cur_password)


def create_access_token(data: dict):
    payload = data.copy()
    cur_time = datetime.now(timezone.utc)
    expire = cur_time + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({'exp': expire, 'iat': cur_time, 'type': 'access'})

    return jwt.encode(payload, SECRET_KEY, ALGORITHM)


def create_refresh_token(data: dict):
    payload = data.copy()
    cur_time = datetime.now(timezone.utc)
    expire = cur_time + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload.update({'exp': expire, 'iat': cur_time, 'type': 'refresh'})

    return jwt.encode(payload, SECRET_KEY, ALGORITHM)


def decode_token(token: str, type: str):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get('sub'))
        type_token = payload.get('type')

        if type_token != type:
            raise HTTPException(
                status_code=401,
                detail='Incorrect token',
                headers={'WWW-Authenticate': 'Bearer'},
            )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail='Incorrect token',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail='Incorrect token',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail='Incorrect token',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    return user_id