from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Union


class RespGetUser(BaseModel):
    id: str
    user_name: str
    passport_id: str
    created_at: datetime


class RespGetPlan(BaseModel):
    id: str
    expiry_date: datetime
    user_id: str


class ReqAddBalanceUpdate(BaseModel):
    user_id: str
    amount: int


class ReqAddPostBalanceIssue:
    user_id: str
    amount: int
