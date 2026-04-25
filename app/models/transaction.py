from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TransferModel(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    sender: Mapped["UserModel"] = relationship(  # noqa: F821
        foreign_keys=[from_user_id], back_populates="sent_transfers"
    )
    receiver: Mapped["UserModel"] = relationship(  # noqa: F821
        foreign_keys=[to_user_id], back_populates="received_transfers"
    )


class PurchaseModel(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    pub_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user: Mapped["UserModel"] = relationship(back_populates="purchases")  # noqa: F821
    item: Mapped["ItemModel"] = relationship(back_populates="purchases")  # noqa: F821
