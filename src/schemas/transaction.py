from pydantic import BaseModel


class SendSchema(BaseModel):
    user: str
    amount: int
