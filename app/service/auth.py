from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository.user import UserRepository
from ..schemas.user import UserDBSchema, UserInSchema
from ..utils.security import (
    create_access_token,
    create_refresh_token,
    delete_refresh_token,
    get_refresh_token,
    hash_password,
    verify_password,
)


class AuthService:
    @staticmethod
    async def register(session: AsyncSession, user_data: UserInSchema) -> None:
        db_dict = UserDBSchema(**user_data.model_dump()).model_dump()
        db_dict["password"] = hash_password(user_data.password)
        try:
            await UserRepository.create(session, db_dict)
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь уже существует.",
            )

    @staticmethod
    async def login(session: AsyncSession, username: str, password: str) -> dict:
        user = await UserRepository.get_by_username(session, username)
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизован."
            )
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = await create_refresh_token(str(user.id))
        return {"access_token": access_token, "refresh_token": refresh_token}

    @staticmethod
    async def refresh(user_id: str) -> str:
        token = await get_refresh_token(user_id)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизован."
            )
        return create_access_token({"sub": user_id})

    @staticmethod
    async def change_password(
        session: AsyncSession,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> None:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено."
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Пользователь неактивен.",
            )
        if not verify_password(old_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный запрос."
            )
        await UserRepository.update_password(session, user.id, hash_password(new_password))

    @staticmethod
    async def logout(user_id: str) -> None:
        await delete_refresh_token(user_id)
