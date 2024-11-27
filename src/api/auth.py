import pyotp
from fastapi import APIRouter, HTTPException, Depends, status, security
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from src.db import user, auth
from src.db import redis_client as redis
from src.schemas import auth as auth_schema
from src.schemas import common as common_schema
from src.core import auth as auth_core
from src.services import SmsService
from src.core import dependecies
from src.utils import otp
from datetime import datetime

router = APIRouter()
passutil = auth_core.Password()


@router.post("/register", response_model=common_schema.CommonMessage)
async def register(register_data: auth_schema.ReqRegisterUser):

    is_user_name_taken = (
        True
        if await user.get_user_by_user_name(user_name=register_data.user_name)
        is not None
        else False
    )

    if is_user_name_taken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"this username '{register_data.user_name}' is already taken",
        )

    is_phone_number_taken = (
        True
        if await user.get_user_by_phone_number(register_data.phone_number) is not None
        else False
    )

    if is_phone_number_taken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"this phone number '{register_data.phone_number}' is already taken",
        )
    password_hash = passutil.secure_pwd(raw_password=register_data.raw_password)

    totp = pyotp.TOTP(pyotp.random_base32())
    otp_secret = totp.secret

    auth_passport_instance = auth.AuthPassport(
        password_hash=None, otp_secret=otp_secret
    )
    user_instance = user.User(
        user_name=register_data.first_name,
        phone_number=register_data.phone_number,
        created_at=datetime.now(),
        passport_id=auth_passport_instance.id,
    )

    await auth.create_auth(user_id=user_instance.id)
    await auth.create_auth_passport(auth_passport=auth_passport_instance)
    await auth.update_new_password(
        password_hash=password_hash,
        passport_id=auth_passport_instance.id,
        user_id=user_instance.id,
    )

    await user.create_user(user_data=user_instance)
    return {"msg": "Registered"}


@router.post("/login/password", response_model=auth_schema.RespLogin)
async def login_by_password(form_data: OAuth2PasswordRequestForm = Depends()):
    user_name = form_data.username
    password = form_data.password

    user_instance = await user.get_user_by_user_name(user_name=user_name)
    if not user_instance:
        raise HTTPException(status_code=400, detail="Invalid Credentials")

    passport_id = user_instance.get("passport_id")
    auth_passport = await auth.get_auth_passport_by_id(auth_passport_id=passport_id)
    password_hash = auth_passport.get("password_hash")

    is_authenticated = passutil.verify_pwd(plain=password, password_hash=password_hash)

    if not is_authenticated:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    user_id = str(user_instance.get("_id"))
    resp = {
        "access_token": auth_core.create_access_token(user_id=user_id),
        "refresh_token": auth_core.create_refresh_token(user_id=user_id),
        "token_type": "bearer",
    }
    return resp


@router.post("/validate/issue", response_model=common_schema.CommonMessage)
async def issue_otp(user_id=Depends(dependecies.jwt_required)):
    user_instance = await user.get_user_by_id(id=user_id)

    user_id = user_instance.get("_id")
    otp_token = await otp.generate_otp(user_id=user_id)
    sms_service = SmsService()
    sms_service.send_sms(receiver=user_instance.get("phone_number"), message=otp_token)
    return {"msg": "otp sent to the user phone number"}


@router.post("/validate/otp/verify", response_model=common_schema.CommonMessage)
async def verify_otp(given_otp: str, user_id=Depends(dependecies.jwt_required)):
    is_otp_correct = await otp.validate_otp(otp_token=given_otp, user_id=user_id)
    if not is_otp_correct:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    await user.update_user_instance(id=user_id, update_query={"validated": True})
    return {"msg": "the acount has been validated"}


@router.post("/refresh", response_model=auth_schema.RespRefreshToken)
async def refresh_token(
    refresh_token: str, access_token=Depends(dependecies.get_access_token)
):
    # Decode the tokens to extract user information
    decoded_access_token = auth_core.decode_jwt(access_token)
    decoded_refresh_token = auth_core.decode_jwt(refresh_token)

    if not decoded_access_token or not decoded_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    access_token_user_id = decoded_access_token.get("user_id")
    refresh_token_user_id = decoded_refresh_token.get("user_id")

    if access_token_user_id != refresh_token_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to make this request",
        )

    # Check if the refresh token is blacklisted
    if redis.get(refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is blacklisted",
        )

    # Blacklist old tokens
    access_token_exp = decoded_access_token.get("exp")
    refresh_token_exp = decoded_refresh_token.get("exp")
    current_time = datetime.utcnow().timestamp()

    if access_token_exp and int(access_token_exp) > current_time:
        access_token_ttl = int(access_token_exp - current_time)
        redis.setex(access_token, access_token_ttl, "blacklisted")

    if refresh_token_exp and int(refresh_token_exp) > current_time:
        refresh_token_ttl = int(refresh_token_exp - current_time)
        redis.setex(refresh_token, refresh_token_ttl, "blacklisted")

    # Generate new tokens
    resp = auth_core.refresh_token(
        refresh_token=refresh_token, user_id=access_token_user_id
    )

    return resp


@router.post("/logout", response_model=common_schema.CommonMessage)
async def logout(access_token=Depends(dependecies.get_access_token)):

    decoded_token = auth.decode_jwt(access_token)
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    exp = decoded_token.get("exp")
    if not exp:
        raise HTTPException(status_code=401, detail="Invalid token: no expiration")

    current_time = datetime.utcnow().timestamp()
    ttl = int(exp - current_time)
    if ttl <= 0:
        raise HTTPException(status_code=401, detail="Token already expired")

    # Blacklist the token by storing it in Redis with the TTL
    redis.setex(access_token, ttl, "blacklisted")

    return common_schema.CommonMessage(message="Successfully logged out")


@router.post("/Update/role", response_model=common_schema.CommonMessage)
async def change_user_role(
    payload: auth_schema.ReqPostUpdateRole,
    is_admin=Depends(dependecies.admin_is_required),
):
    try:
        if is_admin:
            await user.update_user_instance(
                id=payload.target_user_id, update_query={"role": payload.role}
            )
            return {"msg": "role updated"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
