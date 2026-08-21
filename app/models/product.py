from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, func, Numeric, Computed, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from datetime import datetime
from decimal import Decimal

from app.database import Base


class Product(Base):

    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    saller_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    descriptions: Mapped[str | None] = mapped_column(String(300), nullable=True)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    create_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    update_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    tsv: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            """
            setweight(to_tsvector('english', coalesce(name, '')), 'A')
            ||
            setweight(to_tsvector('english', coalesce(descriptions, '')), 'B')
            """,
            persisted=True
        ),
        nullable=False
    )

    cart_items: Mapped[list['CartItem']] = relationship(
        back_populates = 'product',
        cascade='all, delete-orphan',
    )

    saller: Mapped['User'] = relationship(
        back_populates='product'
    )

    items: Mapped[list['OrderItem']] = relationship(
        back_populates='product',
    )

    __table_args__ = (
        Index('ix_products_tsv_gin', 'tsv', postgresql_using='gin'),
    )

