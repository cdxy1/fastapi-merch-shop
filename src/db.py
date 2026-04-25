from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from src.config import config

Base = declarative_base()


class Database:
    def __init__(self, db_url: Optional[str] = None):
        self.DATABASE_URL = db_url if db_url else config.postgres.connection_string
        self.engine = create_async_engine(self.DATABASE_URL)
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self):
        async with self.async_session() as session:
            yield session

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


database = Database()
