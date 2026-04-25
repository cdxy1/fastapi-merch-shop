from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.db import Database, database
from app.main import app
from app.models.item import ItemModel

TEST_DATABASE = Database("sqlite+aiosqlite:///:memory:")

PRODUCTS_DATA = [
    {"name": "t-shirt", "price": 80},
    {"name": "cup", "price": 20},
    {"name": "book", "price": 50},
    {"name": "pen", "price": 10},
    {"name": "powerbank", "price": 200},
    {"name": "hoody", "price": 300},
    {"name": "umbrella", "price": 200},
    {"name": "socks", "price": 10},
    {"name": "wallet", "price": 50},
    {"name": "pink-hoody", "price": 500},
    {"name": "expensive", "price": 100000},
]


@pytest_asyncio.fixture(autouse=True)
async def create_init_data(session):
    for product_data in PRODUCTS_DATA:
        session.add(ItemModel(**product_data))
    await session.commit()


@pytest.fixture
def client(session):
    async def override_get_session():
        yield session

    app.dependency_overrides[database.get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def session():
    await TEST_DATABASE.create_tables()
    async with TEST_DATABASE.async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
def mock_redis():
    mock = AsyncMock()
    mock.get_value.return_value = "mock_refresh_token"
    mock.set_value.return_value = None
    mock.delete_value.return_value = None
    with patch("app.utils.security.redis_client", mock):
        yield mock
