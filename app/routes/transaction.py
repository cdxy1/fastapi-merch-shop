from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.db import database
from app.schemas.response import ResponseSchema
from app.schemas.transaction import SendSchema
from app.service.transaction import TransactionService
from app.utils.security import decode_access_token

router = APIRouter(tags=["Transaction"])


@router.post("/buy/{item}")
async def buy_item(
    item: str,
    current_user: Annotated[dict, Depends(decode_access_token)],
    session: Annotated[AsyncSession, Depends(database.get_session)],
) -> JSONResponse:
    await TransactionService.buy_item(session, int(current_user["sub"]), item)
    return JSONResponse(
        status_code=200,
        content=ResponseSchema(detail="Успешный ответ.").model_dump(),
    )


@router.post("/sendCoin")
async def send_coin(
    user_info: SendSchema,
    current_user: Annotated[dict, Depends(decode_access_token)],
    session: Annotated[AsyncSession, Depends(database.get_session)],
) -> JSONResponse:
    await TransactionService.send_coin(
        session, int(current_user["sub"]), user_info.user, user_info.amount
    )
    return JSONResponse(
        status_code=200,
        content=ResponseSchema(detail="Успешный ответ.").model_dump(),
    )


@router.get("/info")
async def info(
    current_user: Annotated[dict, Depends(decode_access_token)],
    session: Annotated[AsyncSession, Depends(database.get_session)],
) -> JSONResponse:
    result = await TransactionService.get_info(session, int(current_user["sub"]))
    return JSONResponse(status_code=200, content=result.model_dump())
