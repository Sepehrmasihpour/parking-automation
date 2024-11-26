from pydantic import BaseModel
from datetime import datetime


class RespGetstatus(BaseModel):
    id: str
    expiry_date: datetime
    user_id: str


class ReqPostCreate(BaseModel):
    expiry_date: datetime
