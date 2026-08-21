from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, func, ForeignKey, Numeric
from datetime import datetime
from decimal import Decimal

from app.database import Base


class Cart(Base):

    __tablename__ = 'carts'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    create_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    update_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user: Mapped['User'] = relationship(
        back_populates='cart',
    )

    cart_items: Mapped[list['CartItem']] = relationship(
        back_populates='cart',
        cascade='all, delete-orphan',
    )


