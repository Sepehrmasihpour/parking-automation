from pydantic import BaseModel
from typing import Union, Literal


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


class ReqPostUpdateRole(BaseModel):
    target_user_id: str
    role: Union[Literal["admin"], None]
