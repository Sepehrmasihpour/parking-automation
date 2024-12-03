from pydantic import BaseModel


class CommonMessage(BaseModel):
    msg: str


class Token(BaseModel):
    token: str
