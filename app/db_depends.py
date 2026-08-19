from app.database import AsyncLocalSession

async def get_async_db():
    async with AsyncLocalSession() as session:
        yield session