from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Union


class RespGetUser(BaseModel):
    id: str
    user_name: str
    phone_number: str
    validated: bool
    passport_id: str
    parking_history_id: str
    created_at: datetime


class RespGetPlan(BaseModel):
    id: str
    expiry_date: datetime
    user_id: str
