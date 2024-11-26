from pydantic import BaseModel


class ReqPostEnterExit(BaseModel):
    parking_id: str
    ticket_id: str


class RespPostTicket(BaseModel):
    ticket_id: str
