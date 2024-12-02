from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Union


class RespGetUser(BaseModel):
    id: str
    user_name: str
    created_at: datetime
    balance: int


class RespGetPlan(BaseModel):
    id: str
    expiry_date: datetime
    user_id: str


class ReqAddBalanceUpdate(BaseModel):
    user_id: str
    amount: int


class ReqPostAddBalanceIssue(BaseModel):
    user_id: str
    amount: int
