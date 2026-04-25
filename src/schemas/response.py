from pydantic import BaseModel


class ResponseSchema(BaseModel):
    detail: str


class AccessTokenResponseSchema(ResponseSchema):
    access_token: str


class AuthResponseSchema(AccessTokenResponseSchema):
    refresh_token: str
    token_type: str


class InventoryItem(BaseModel):
    type: str
    quantity: int


class ReceivedCoin(BaseModel):
    fromUser: str
    amount: int


class SentCoin(BaseModel):
    toUser: str
    amount: int


class CoinHistory(BaseModel):
    received: list[ReceivedCoin]
    sent: list[SentCoin]


class UserInfoResponse(BaseModel):
    coins: int
    inventory: list[InventoryItem]
    CoinHistory: CoinHistory
