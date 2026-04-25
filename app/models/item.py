from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ItemModel(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    price: Mapped[int]

    purchases: Mapped[List["PurchaseModel"]] = relationship(back_populates="item")  # noqa: F821
