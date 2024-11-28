from pydantic import BaseModel


class CommonMessage(BaseModel):
    msg: str
