from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import DecodeError
from passlib.context import CryptContext

from app.config import config
from app.utils.redis import redis_client

pwd_context = CryptContext(["bcrypt"])
oauth2_schema = OAuth2PasswordBearer("/auth")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, config.security.jwt_secret_key, config.security.jwt_algorithm
    )


async def create_refresh_token(user_id: str) -> str:
    expire = timedelta(days=30)
    encoded_jwt = jwt.encode(
        {"sub": user_id},
        config.security.jwt_secret_key,
        config.security.jwt_algorithm,
    )
    await redis_client.set_value(user_id, encoded_jwt, expire)
    return encoded_jwt


async def get_refresh_token(user_id: str) -> str | None:
    return await redis_client.get_value(user_id)


async def delete_refresh_token(user_id: str) -> None:
    await redis_client.delete_value(user_id)


def decode_access_token(token: Annotated[str, Depends(oauth2_schema)]) -> dict:
    try:
        payload = jwt.decode(
            token, config.security.jwt_secret_key, [config.security.jwt_algorithm]
        )
        exp = payload.get("exp")
        if not exp or datetime.now(timezone.utc) >= datetime.fromtimestamp(
            exp, tz=timezone.utc
        ):
            raise HTTPException(status_code=401, detail="Token expired or invalid")
        return payload
    except DecodeError:
        raise HTTPException(status_code=401, detail="Token decode error")


def user_id_from_token(token: Annotated[str, Depends(oauth2_schema)]) -> str:
    try:
        payload = jwt.decode(
            token, config.security.jwt_secret_key, [config.security.jwt_algorithm]
        )
        return payload.get("sub")
    except DecodeError:
        raise HTTPException(status_code=401, detail="Token decode error")
