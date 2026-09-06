from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DateTime, func, UniqueConstraint
from datetime import datetime

from app.database import Base


class Category(Base):

    __tablename__ = 'categoryes'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey('categoryes.id'), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    create_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    update_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    parent: Mapped['Category | None'] = relationship(
        back_populates='childs',
        remote_side=id,
    )

    childs: Mapped[list['Category']] = relationship(
        back_populates='parent',
        single_parent=True,
    )

    products: Mapped[list['Product']] = relationship(
        back_populates='category'
    )

    __table_args__ = (
        UniqueConstraint('name', 'parent_id', name='uq_category_name_parent'),
    )

