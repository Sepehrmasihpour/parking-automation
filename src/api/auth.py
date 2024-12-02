import pyotp
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from src.db import user, auth
from src.db import redis_client as redis
from src.schemas import auth as auth_schema
from src.schemas import common as common_schema
from src.core import auth as auth_core
from src.core import dependecies
from datetime import datetime
import time

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
    password_hash = passutil.secure_pwd(raw_password=register_data.raw_password)

    auth_passport_instance = auth.AuthPassport(password_hash=None)
    user_instance = user.User(
        user_name=register_data.user_name,
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
    """
    OAuth2-compliant login endpoint using form-encoded data.
    """
    # Extract the username and password from the form data
    user_name = form_data.username
    password = form_data.password

    # Fetch the user from the database
    user_instance = await user.get_user_by_user_name(user_name=user_name)
    if not user_instance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials"
        )

    # Validate the password
    passport_id = user_instance.get("passport_id")
    auth_passport = await auth.get_auth_passport_by_id(auth_passport_id=passport_id)
    password_hash = auth_passport.get("password_hash")

    is_authenticated = passutil.verify_pwd(plain=password, password_hash=password_hash)
    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Generate access and refresh tokens
    user_id = str(user_instance.get("_id"))
    resp = {
        "access_token": auth_core.create_access_token(user_id=user_id),
        "refresh_token": auth_core.create_refresh_token(user_id=user_id),
    }
    return resp


@router.post("/refresh", response_model=auth_schema.RespRefreshToken)
async def refresh_token(refresh_token: auth_schema.ReqPostRefresh):
    # Check if the refresh token is blacklisted
    redis_value = await redis.get(refresh_token.refresh_token)
    if redis_value is not None and redis_value.decode("utf-8") == "blacklisted":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is blacklisted",
        )

    decoded_refresh_token = auth_core.decode_jwt(refresh_token.refresh_token)
    if not decoded_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    token_user_id = decoded_refresh_token.get("user_id")
    refresh_token_exp = decoded_refresh_token.get("exp")
    current_time = int(time.time())

    refresh_token_ttl = int(refresh_token_exp - current_time)
    if refresh_token_ttl <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # Blacklist the used refresh token
    await redis.setex(refresh_token.refresh_token, refresh_token_ttl, "blacklisted")

    # Generate new tokens
    resp = dict(
        access_token=auth_core.create_access_token(token_user_id),
        refresh_token=auth_core.create_refresh_token(token_user_id),
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
    await redis.setex(access_token, ttl, "blacklisted")

    return common_schema.CommonMessage(message="Successfully logged out")
