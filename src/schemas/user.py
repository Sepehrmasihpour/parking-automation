from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Union


class RespGetUser(BaseModel):
    user_name: str
    balance: int


class RespGetPlan(BaseModel):
    id: str
    expiry_date: datetime
    user_id: str


class ReqAddBalanceUpdate(BaseModel):
    user_id: str
    amount: int


class ReqPostAddBalance(BaseModel):
    user_id: str
    amount: int


class RespPostAddBalanceCreate(BaseModel):
    token: str
