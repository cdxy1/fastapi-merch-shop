from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import ItemModel


class ItemRepository:
    @staticmethod
    async def get_by_name(session: AsyncSession, name: str) -> ItemModel | None:
        result = await session.execute(select(ItemModel).where(ItemModel.name == name))
        return result.scalars().first()
