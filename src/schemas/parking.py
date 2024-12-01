from pydantic import BaseModel


class ReqPostEnterExit(BaseModel):
    id: str


class RespPostTicket(BaseModel):
    ticket_id: str


class ReqPostTicketUpdateExpiry(BaseModel):
    ticket_id: str
    expiry_date: str
