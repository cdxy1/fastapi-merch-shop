from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from src.db import database
from src.schemas.response import (
    AccessTokenResponseSchema,
    AuthResponseSchema,
    ResponseSchema,
)
from src.schemas.user import ChangePasswordScheme, UserInSchema
from src.service.auth import AuthService
from src.utils.security import decode_access_token, user_id_from_token

router = APIRouter(tags=["Auth"])


@router.post("/register")
async def register(
    user: UserInSchema,
    session: Annotated[AsyncSession, Depends(database.get_session)],
) -> JSONResponse:
    await AuthService.register(session, user)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=ResponseSchema(detail="Пользователь зарегистрирован.").model_dump(),
    )


@router.post("/auth")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(database.get_session)],
) -> JSONResponse:
    tokens = await AuthService.login(session, form_data.username, form_data.password)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=AuthResponseSchema(
            detail="Успешная аутентификация.",
            token_type="bearer",
            **tokens,
        ).model_dump(),
    )


@router.post("/refresh")
async def refresh_access_token(
    current_user: Annotated[str, Depends(user_id_from_token)],
) -> JSONResponse:
    token = await AuthService.refresh(current_user)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=AccessTokenResponseSchema(
            detail="Успешный ответ.", access_token=token
        ).model_dump(),
    )


@router.patch("/change_password")
async def change_password(
    passwords: ChangePasswordScheme,
    current_user: Annotated[dict, Depends(decode_access_token)],
    session: Annotated[AsyncSession, Depends(database.get_session)],
) -> JSONResponse:
    await AuthService.change_password(
        session,
        int(current_user["sub"]),
        passwords.old_password,
        passwords.new_password,
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ResponseSchema(detail="Успешный ответ.").model_dump(),
    )


@router.delete("/logout")
async def logout(
    current_user: Annotated[dict, Depends(decode_access_token)],
) -> JSONResponse:
    await AuthService.logout(current_user["sub"])
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ResponseSchema(detail="Успешный ответ.").model_dump(),
    )
