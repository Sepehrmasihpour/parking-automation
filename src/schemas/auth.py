from pydantic import BaseModel, EmailStr
from typing import Union, Literal


class ReqRegisterUser(BaseModel):
    email: EmailStr
    raw_password: str


class ReqLoginPassword(BaseModel):
    username: str
    password: str


class RespLogin(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RespRefreshToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ReqPostRefresh(BaseModel):
    refresh_token: str


class ReqPostValidateVerify(BaseModel):
    otp: str
