from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from src.db import role


class ReqRegisterUser(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    raw_password: str


class ReqLoginPassword(BaseModel):
    phone_number: str
    password: str


class ReqLoginOtpIssue(BaseModel):
    phone_number: str


class ReqLoginVerifyOtp(BaseModel):
    otp: str
    phone_number: str


class RespLogin(BaseModel):
    access_token: str
    refresh_token: str


class RespRefreshToken(BaseModel):
    access_token: str
    refresh_token: str


class RespUpdateRole(BaseModel):
    id: str
    role: str


class RoleUpdatePayload(BaseModel):
    role: Literal["base", "building_manager"]


class ReqUpdateRole(BaseModel):
    target_id: str
    update_payload: RoleUpdatePayload


class ReqLogout(BaseModel):
    access_token: str
    refresh_token: str
