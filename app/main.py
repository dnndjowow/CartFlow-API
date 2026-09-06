from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.user import router as user_router
from app.routers.product import router as product_router
from app.routers.cart import router as cart_router
from app.routers.order import router as order_router
from app.routers.category import router as category_router
from app.config import BASE_DIR

app = FastAPI()

app.mount('/media', StaticFiles(directory=BASE_DIR / 'media'), name='media')

app.include_router(user_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(category_router)
