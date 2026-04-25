import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import UserModel
from src.schemas.response import (
    ResponseSchema,
)
from src.schemas.user import UserInSchema
from src.utils.security import verify_password

ACCESS_TOKEN = None


@pytest.mark.asyncio
async def test_register(client, session: AsyncSession):
    user_data = UserInSchema(username="test_user", password="password")

    response = client.post("/register", json=user_data.model_dump())

    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response.json()
        == ResponseSchema(detail="Пользователь зарегистрирован.").model_dump()
    )

    result = await session.execute(
        select(UserModel).where(UserModel.username == "test_user")
    )
    user = result.scalars().first()
    assert user is not None
    assert user.username == "test_user"
    assert verify_password("password", user.password)


@pytest.mark.asyncio
async def test_login(client, session: AsyncSession, mock_redis):
    global ACCESS_TOKEN

    form_data = {"username": "test_user", "password": "password"}
    response = client.post("/auth", data=form_data)

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    ACCESS_TOKEN = response.json()["access_token"]

    response_data = response.json()
    assert response_data["detail"] == "Успешная аутентификация."
    assert response_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token(client, mock_redis):
    mock_redis.set_value = "refresh_token"

    response = client.post(
        "/refresh",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()

    response_data = response.json()
    assert response_data["detail"] == "Успешный ответ."


@pytest.mark.asyncio
async def test_change_password(client, session: AsyncSession):
    passwords = {"old_password": "password", "new_password": "new_password"}
    response = client.patch(
        "/change_password",
        json=passwords,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == ResponseSchema(detail="Успешный ответ.").model_dump()

    result = await session.execute(
        select(UserModel).where(UserModel.username == "test_user")
    )
    user = result.scalars().first()
    assert verify_password("new_password", user.password)


@pytest.mark.asyncio
async def test_logout(client, mock_redis):
    mock_redis.delete_value.return_value = True

    response = client.delete(
        "/logout",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == ResponseSchema(detail="Успешный ответ.").model_dump()


@pytest.mark.asyncio
async def test_register_existing_user(client, session: AsyncSession):
    user_data = UserInSchema(username="test_user", password="password")
    response = client.post("/register", json=user_data.model_dump())
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Пользователь уже существует."


@pytest.mark.asyncio
async def test_login_invalid_credentials(client, session: AsyncSession):
    form_data = {"username": "test_user", "password": "wrong_password"}
    response = client.post("/auth", data=form_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Неавторизован."


@pytest.mark.asyncio
async def test_change_password_incorrect_old_password(client, session: AsyncSession):
    passwords = {"old_password": "wrong_password", "new_password": "new_password"}
    response = client.patch(
        "/change_password",
        json=passwords,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Неверный запрос."
