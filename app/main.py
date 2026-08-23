from fastapi import FastAPI

from app.routers.user import router as user_router
from app.routers.product import router as product_router

app = FastAPI()

app.include_router(user_router)
app.include_router(product_router)
