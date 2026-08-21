from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint, Numeric
from decimal import Decimal

from app.database import Base


class CartItem(Base):

    __tablename__ = 'cart_items'

    __table_args__ = (
        UniqueConstraint('cart_id', 'product_id', name='uq_cart_items_cart_product'),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey('carts.id', ondelete='CASCADE'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    quantity: Mapped[int] = mapped_column(default=1, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)

    cart: Mapped['Cart'] = relationship(
        back_populates = 'cart_items',
    )

    product: Mapped['Product'] = relationship(
        back_populates = 'cart_items',
    )

