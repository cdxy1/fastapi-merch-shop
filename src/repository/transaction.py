from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.purchase import PurchaseModel
from src.models.transaction import TransferModel


class TransactionRepository:
    @staticmethod
    async def get_transfers_by_user(
        session: AsyncSession, user_id: int
    ) -> list[TransferModel]:
        result = await session.execute(
            select(TransferModel)
            .where(
                (TransferModel.from_user_id == user_id)
                | (TransferModel.to_user_id == user_id)
            )
            .options(
                selectinload(TransferModel.sender),
                selectinload(TransferModel.receiver),
            )
            .order_by(TransferModel.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_purchases_by_user(
        session: AsyncSession, user_id: int
    ) -> list[PurchaseModel]:
        result = await session.execute(
            select(PurchaseModel)
            .where(PurchaseModel.user_id == user_id)
            .options(selectinload(PurchaseModel.item))
            .order_by(PurchaseModel.pub_date.desc())
        )
        return result.scalars().all()
