from pydantic import BaseModel, Field


class SendSchema(BaseModel):
    user: str 
    amount: int = Field(gt=0)
