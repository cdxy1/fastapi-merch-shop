from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from ..db import database
from ..models.user import UserModel
from ..schemas.response import (
    AccessTokenResponseSchema,
    AuthResponseSchema,
    ResponseSchema,
)
from ..schemas.user import ChangePasswordScheme, UserDBSchema, UserInSchema
from ..utils.info_utils import get_user_info
from ..utils.redis import redis_client
from ..utils.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    user_id_from_token,
    verify_password,
)

router = APIRouter(tags=["Auth"])


@router.post("/register")
async def register(
    user: UserInSchema,
    session: Annotated[AsyncSession, Depends(database.get_session)],
) -> JSONResponse:
    user_dict = user.model_dump()
    user_db_dict = UserDBSchema(**user_dict).model_dump()

    user_db_dict["password"] = hash_password(user.password)
    new_user = UserModel(**user_db_dict)
    session.add(new_user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже существует."
        )
    response = ResponseSchema(detail="Пользователь зарегистрирован.")
    return JSONResponse(
        status_code=status.HTTP_201_CREATED, content=response.model_dump()
    )


@router.post("/auth")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(database.get_session)],
) -> JSONResponse:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизован."
    )

    result = await session.execute(
        select(UserModel).where(UserModel.username == form_data.username)
    )
    user = result.scalars().first()
    if user and verify_password(form_data.password, user.password):
        token = create_access_token({"sub": str(user.id)})
        refresh_token = await create_refresh_token(str(user.id))
        response = AuthResponseSchema(
            detail="Успешная аутентификация.",
            access_token=token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=response.model_dump()
        )
    else:
        raise credentials_exc


@router.post("/refresh")
async def refresh_access_token(
    current_user: Annotated[str, Depends(user_id_from_token)],
):
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Неавторизован."
    )

    if not current_user:
        raise exc

    refresh_token = await redis_client.get_value(current_user)
    if not refresh_token:
        raise exc

    payload = {"sub": current_user}

    token = create_access_token(payload)
    response = AccessTokenResponseSchema(detail="Успешный ответ.", access_token=token)
    return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump())


@router.patch("/change_password")
async def change_password(
    passwords: ChangePasswordScheme,
    current_user: Annotated[dict, Depends(decode_access_token)],
    session: Annotated[AsyncSession, Depends(database.get_session)],
) -> JSONResponse:
    user_id = current_user.get("sub")
    user = await get_user_info(int(user_id), session)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено.")

    if not verify_password(passwords.old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный запрос."
        )

    new_hashed_password = hash_password(passwords.new_password)
    update_result = (
        update(UserModel)
        .filter(UserModel.id == user.id)
        .values(password=new_hashed_password)
    )
    await session.execute(update_result)
    await session.commit()

    response = ResponseSchema(detail="Успешный ответ.")
    return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump())


@router.delete("/logout")
async def logout(
    current_user: Annotated[dict, Depends(decode_access_token)],
) -> JSONResponse:
    user_id = current_user.get("sub")
    await redis_client.delete_value(user_id)
    response = ResponseSchema(detail="Успешный ответ.")
    return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump())
