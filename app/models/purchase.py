from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PurchaseModel(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    pub_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user: Mapped["UserModel"] = relationship(back_populates="purchases")  # noqa: F821
    item: Mapped["ItemModel"] = relationship(back_populates="purchases")  # noqa: F821
