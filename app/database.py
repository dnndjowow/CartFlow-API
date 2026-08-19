from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import DATABASE_URL

async_engine = create_async_engine(DATABASE_URL)
AsyncLocalSession = async_sessionmaker(bind=async_sessionmaker, expire_on_commit=False)

class Base(DeclarativeBase):
    pass