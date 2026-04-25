from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


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
