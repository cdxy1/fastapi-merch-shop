import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.purchase import PurchaseModel
from app.models.user import UserModel
from app.schemas.response import (
    ResponseSchema,
)
from app.schemas.transaction import SendSchema
from app.schemas.user import UserInSchema

ACCESS_TOKEN = None


@pytest.mark.asyncio
async def test_register(client, session: AsyncSession):
    user_data = UserInSchema(username="test_user", password="password")

    client.post("/register", json=user_data.model_dump())


@pytest.mark.asyncio
async def test_login(client, session: AsyncSession, mock_redis):
    global ACCESS_TOKEN

    form_data = {"username": "test_user", "password": "password"}
    response = client.post("/auth", data=form_data)
    if response.status_code != status.HTTP_200_OK:
        form_data["password"] = "new_password"
        response = client.post("/auth", data=form_data)
    ACCESS_TOKEN = response.json()["access_token"]


@pytest.mark.asyncio
async def test_buy_item_success(client, session: AsyncSession):
    response = client.post(
        "/buy/t-shirt",
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
    assert user is not None
    assert user.balance == 920

    result = await session.execute(
        select(PurchaseModel).options(
            selectinload(PurchaseModel.user), selectinload(PurchaseModel.item)
        )
    )
    purchase = result.scalars().first()
    assert purchase is not None

    assert purchase.user.username == "test_user"
    assert purchase.item.name == "t-shirt"


@pytest.mark.asyncio
async def test_buy_item_insufficient_balance(client, session: AsyncSession):
    response = client.post(
        "/buy/expensive",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Неверный запрос."


@pytest.mark.asyncio
async def test_buy_item_not_found(client, session: AsyncSession):
    response = client.post(
        "/buy/non-existent-item",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Не найдено."


@pytest.mark.asyncio
async def test_send_coin_success(client, session: AsyncSession):
    to_user = UserModel(
        username="recipient_user",
        password="hashed_password",
        balance=0,
        role="user",
        is_active=True,
    )
    session.add(to_user)
    await session.commit()

    user_info = SendSchema(user="recipient_user", amount=50)
    response = client.post(
        "/sendCoin",
        json=user_info.model_dump(),
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
    from_user = result.scalars().first()
    assert from_user.balance == 870

    result = await session.execute(
        select(UserModel).where(UserModel.username == "recipient_user")
    )
    to_user = result.scalars().first()
    assert to_user.balance == 50


@pytest.mark.asyncio
async def test_send_coin_insufficient_balance(client, session: AsyncSession):
    user_info = SendSchema(user="recipient_user", amount=100000)
    response = client.post(
        "/sendCoin",
        json=user_info.model_dump(),
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Неверный запрос."


@pytest.mark.asyncio
async def test_send_coin_recipient_not_found(client, session: AsyncSession):
    user_info = SendSchema(user="non-existent-user", amount=50)
    response = client.post(
        "/sendCoin",
        json=user_info.model_dump(),
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Не найдено."


@pytest.mark.asyncio
async def test_info_success(client, session: AsyncSession):
    response = client.get(
        "/info",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["coins"] == 870
    assert response_data["inventory"] == [{"type": "t-shirt", "quantity": 1}]
    assert response_data["CoinHistory"]["received"] == []
    assert response_data["CoinHistory"]["sent"] == [
        {"toUser": "recipient_user", "amount": 50}
    ]
