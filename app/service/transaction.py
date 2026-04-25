from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import TransferModel
from app.models.purchase import PurchaseModel
from app.repository.item import ItemRepository
from app.repository.transaction import TransactionRepository
from app.repository.user import UserRepository
from app.schemas.response import (
    CoinHistory,
    InventoryItem,
    ReceivedCoin,
    SentCoin,
    UserInfoResponse,
)


class TransactionService:
    @staticmethod
    async def buy_item(session: AsyncSession, user_id: int, item_name: str) -> None:
        async with session.begin():
            user = await UserRepository.get_by_id(session, user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено."
                )

            item = await ItemRepository.get_by_name(session, item_name)
            if item is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено."
                )

            if user.balance < item.price:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный запрос."
                )

            user.balance -= item.price
            session.add(PurchaseModel(user_id=user.id, item_id=item.id))

    @staticmethod
    async def send_coin(
        session: AsyncSession, from_user_id: int, to_username: str, amount: int
    ) -> None:
        async with session.begin():
            from_user = await UserRepository.get_by_id(session, from_user_id)
            if not from_user or not from_user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено."
                )

            if from_user.username == to_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный запрос."
                )

            to_user = await UserRepository.get_by_username(session, to_username)
            if not to_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено."
                )

            if from_user.balance < amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный запрос."
                )

            from_user.balance -= amount
            to_user.balance += amount
            session.add(
                TransferModel(
                    from_user_id=from_user.id,
                    to_user_id=to_user.id,
                    amount=amount,
                )
            )

    @staticmethod
    async def get_info(session: AsyncSession, user_id: int) -> UserInfoResponse:
        user = await UserRepository.get_by_id(session, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено."
            )

        transfers = await TransactionRepository.get_transfers_by_user(session, user_id)
        purchases = await TransactionRepository.get_purchases_by_user(session, user_id)

        item_counts = _count_items(purchases)
        transfer_data = _process_transfers(transfers, user_id)

        return UserInfoResponse(
            coins=user.balance,
            inventory=[
                InventoryItem(type=name, quantity=count)
                for name, count in item_counts.items()
            ],
            CoinHistory=CoinHistory(
                received=[
                    ReceivedCoin(fromUser=u, amount=a)
                    for u, a in transfer_data["received"].items()
                ],
                sent=[
                    SentCoin(toUser=u, amount=a)
                    for u, a in transfer_data["sent"].items()
                ],
            ),
        )


def _count_items(purchases: list[PurchaseModel]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for purchase in purchases:
        name = purchase.item.name
        counts[name] = counts.get(name, 0) + 1
    return counts


def _process_transfers(
    transfers: list[TransferModel], user_id: int
) -> dict[str, dict[str, int]]:
    received: dict[str, int] = {}
    sent: dict[str, int] = {}
    for transfer in transfers:
        if transfer.to_user_id == user_id:
            received[transfer.sender.username] = (
                received.get(transfer.sender.username, 0) + transfer.amount
            )
        elif transfer.from_user_id == user_id:
            sent[transfer.receiver.username] = (
                sent.get(transfer.receiver.username, 0) + transfer.amount
            )
    return {"received": received, "sent": sent}
