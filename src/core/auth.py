import os
import jwt
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from passlib.context import CryptContext
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from src.db import redis_client as redis
from fastapi import HTTPException, status
from typing import Optional

# Load environment variables
load_dotenv()

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY")  # Matches .env variable
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")  # Defaults to HS256
JWT_ACCESS_TOKEN_EXPIRY_PER_HOURS = int(os.getenv("JWT_ACCESS_HOURS"))
JWT_REFRESH_TOKEN_EXPIRY_PER_HOURS = int(os.getenv("JWT_REFRESH_HOURS"))


class Password:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def secure_pwd(self, raw_password: str) -> str:
        """
        Hash a plain-text password securely.
        """
        return self.pwd_context.hash(raw_password)

    def verify_pwd(self, plain: str, password_hash: str) -> bool:
        """
        Verify if a plain-text password matches the hashed password.
        """
        return self.pwd_context.verify(plain, password_hash)


def create_access_token(user_id: str, expires_delta: int = None) -> str:
    """
    Create a JWT access token with an optional expiration time.
    """
    expiry = datetime.now() + (
        timedelta(hours=expires_delta)
        if expires_delta is not None
        else timedelta(hours=JWT_ACCESS_TOKEN_EXPIRY_PER_HOURS)
    )
    to_encode = {"exp": expiry, "user_id": user_id}
    try:
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    except Exception as e:
        raise ValueError(f"Error creating access token: {str(e)}")
    return encoded_jwt


def create_refresh_token(user_id: str, expires_delta: int = None) -> str:
    """
    Create a JWT refresh token with an optional expiration time.
    """
    expiry = datetime.now() + (
        timedelta(hours=expires_delta)
        if expires_delta is not None
        else timedelta(hours=JWT_REFRESH_TOKEN_EXPIRY_PER_HOURS)
    )
    to_encode = {"exp": expiry, "user_id": user_id}
    try:
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    except Exception as e:
        raise ValueError(f"Error creating refresh token: {str(e)}")
    return encoded_jwt


def create_token(user_id: str) -> dict:
    """
    Generate both access and refresh tokens for a user.
    """
    try:
        return {
            "access_token": create_access_token(user_id=user_id),
            "refresh_token": create_refresh_token(user_id=user_id),
        }
    except Exception as e:
        raise ValueError(f"Error creating tokens: {str(e)}")


@router.post("/logout", response_model=common_schema.CommonMessage)
async def logout(access_token=Depends(dependecies.get_access_token)):
    try:
        # Attempt to decode the JWT
        decoded_token = auth_core.decode_jwt(access_token)
        exp = decoded_token.get("exp")
        current_time = datetime.utcnow().timestamp()
        ttl = int(exp - current_time)

        if ttl <= 0:
            return {"msg": "token is already expired"}

        # Blacklist the token by storing it in Redis with the TTL
        await redis.setex(access_token, ttl, "blacklisted")
        return common_schema.CommonMessage(message="Successfully logged out")

    except HTTPException as e:
        # Handle specific HTTP 401 error due to expired token
        if (
            e.status_code == status.HTTP_401_UNAUTHORIZED
            and "Token has expired" in e.detail
        ):
            return {"msg": "token is already expired"}
        # Re-raise other HTTP exceptions
        raise e
    except Exception as e:
        # Re-raise any other exceptions for further handling
        raise e


def parse_authorization_token(token: str) -> str:
    """
    Parse a Bearer token from an authorization header.
    """
    try:
        parts = token.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ValueError("Invalid token format. Expected 'Bearer <token>'.")
        return parts[1]
    except Exception as e:
        raise ValueError(f"Error parsing token: {str(e)}")
