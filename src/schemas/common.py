from pydantic import BaseModel


class CommonMessage(BaseModel):
    message: str
