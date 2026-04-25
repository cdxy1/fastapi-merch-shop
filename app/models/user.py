from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str]
    balance: Mapped[int] = mapped_column(default=1000, nullable=False)
    is_active: Mapped[bool]

    sent_transfers: Mapped[List["TransferModel"]] = relationship(  # noqa: F821
        foreign_keys="TransferModel.from_user_id", back_populates="sender"
    )
    received_transfers: Mapped[List["TransferModel"]] = relationship(  # noqa: F821
        foreign_keys="TransferModel.to_user_id", back_populates="receiver"
    )
    purchases: Mapped[List["PurchaseModel"]] = relationship(back_populates="user")  # noqa: F821
