from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.routes.auth import router as auth_router
from app.routes.transaction import router as transaction_router
from app.schemas.response import ResponseSchema
from app.utils.redis import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.connect()
    yield
    await redis_client.close()


app = FastAPI(lifespan=lifespan, root_path="/api")


app.include_router(auth_router)
app.include_router(transaction_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 400:
        error_400_response = ResponseSchema(detail="Неверный запрос.")
        return JSONResponse(status_code=400, content=error_400_response.model_dump())
    if exc.status_code == 401:
        error_401_response = ResponseSchema(detail="Неавторизован.")
        return JSONResponse(status_code=401, content=error_401_response.model_dump())
    if exc.status_code == 404:
        error_404_response = ResponseSchema(detail="Не найдено.")
        return JSONResponse(status_code=404, content=error_404_response.model_dump())
    if exc.status_code == 409:
        error_409_response = ResponseSchema(detail="Пользователь уже существует.")
        return JSONResponse(status_code=409, content=error_409_response.model_dump())
    if exc.status_code == 500:
        error_500_response = ResponseSchema(detail="Внутренняя ошибка сервера.")
        return JSONResponse(status_code=500, content=error_500_response.model_dump())
