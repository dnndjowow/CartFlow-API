from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy import DateTime, func

from app.database import Base


class User(Base):

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False, default='customer')
    create_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    update_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    cart: Mapped['Cart'] = relationship(
        back_populates='user',
        cascade='all, delete-orphan',
    )

    order: Mapped[list['Order']] = relationship(
        back_populates='user',
    )

    product: Mapped[list['Product']] = relationship(
        back_populates='seller',
    )
