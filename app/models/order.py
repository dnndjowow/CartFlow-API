from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, func, Numeric, ForeignKey
from datetime import datetime
from decimal import Decimal

from app.database import Base


class Order(Base):

    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(default='pending',nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    create_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    update_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user: Mapped['User'] = relationship(
        back_populates='order'
    )

    items: Mapped[list['OrderItem']] = relationship(
        back_populates='order',
        cascade='all, delete-orphan',
    )





