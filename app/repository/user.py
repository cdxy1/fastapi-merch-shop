from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import UserModel


class UserRepository:
    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> UserModel | None:
        result = await session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> UserModel | None:
        result = await session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        return result.scalars().first()

    @staticmethod
    async def create(session: AsyncSession, user_data: dict) -> UserModel:
        user = UserModel(**user_data)
        session.add(user)
        await session.commit()
        return user

    @staticmethod
    async def update_password(
        session: AsyncSession, user_id: int, new_hash: str
    ) -> None:
        await session.execute(
            update(UserModel).where(UserModel.id == user_id).values(password=new_hash)
        )
        await session.commit()
