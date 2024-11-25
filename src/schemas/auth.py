from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from src.db import role


class ReqRegisterUser(BaseModel):
    user_name: str
    phone_number: str
    raw_password: str


class ReqLoginPassword(BaseModel):
    user_name: str
    password: str


class RespLogin(BaseModel):
    access_token: str
    refresh_token: str


class RespRefreshToken(BaseModel):
    access_token: str
    refresh_token: str
