from pydantic import BaseModel
from typing import Union, Literal


class ReqRegisterUser(BaseModel):
    user_name: str
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


class ReqPostUpdateRole(BaseModel):
    target_user_id: str
    role: Union[Literal["admin"], None]


class ReqPostRefresh(BaseModel):
    refresh_token: str


class ReqPostValidateVerify(BaseModel):
    otp: str
