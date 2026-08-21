from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Numeric, ForeignKey, UniqueConstraint
from datetime import datetime
from decimal import Decimal

from app.database import Base


class OrderItem(Base):

    __tablename__ = 'orderitems'

    __table_args__ = (
        UniqueConstraint('product_id', 'order_id', name='uq_product_order'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)

    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)

    product: Mapped['Product'] = relationship(
        back_populates='items',
    )

    order: Mapped['Order'] = relationship(
        back_populates='items',
    )
    
