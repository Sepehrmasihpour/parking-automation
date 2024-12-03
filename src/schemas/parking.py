from pydantic import BaseModel
from typing import Literal


class ReqPostEnterExit(BaseModel):
    id: str
    type: Literal["ticket", "user"]


class RespPostTicket(BaseModel):
    token: str


class ReqPostTicketUpdateExpiry(BaseModel):
    ticket_id: str
    expiry_date: str
