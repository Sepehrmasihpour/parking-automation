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


def decode_jwt(jwtoken: str):
    """
    Decode a JWT token and return its payload.
    """
    try:
        payload = jwt.decode(jwtoken, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except InvalidTokenError:
        print("Invalid token.")
        return None
    except Exception as e:
        print(f"Error decoding token: {str(e)}")
        return None


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


def encode_parking_response(
    ticket_id: Optional[str] = None, user_id: Optional[str] = None
) -> str:
    """
    Create a JWT token encoding either a ticket_id or a user_id.
    Exactly one of ticket_id or user_id must be provided.
    """
    # Enforce XOR condition between ticket_id and user_id
    if (ticket_id is None and user_id is None) or (
        ticket_id is not None and user_id is not None
    ):
        raise ValueError("Exactly one of ticket_id or user_id must be provided.")

    # Include the provided identifier in the token payload
    if ticket_id is not None:
        to_encode = {"ticket_id": ticket_id}
    else:
        to_encode = {"user_id": user_id}

    try:
        # Encode the JWT token
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    except Exception as e:
        raise ValueError(f"Error creating access token: {str(e)}")

    return encoded_jwt


def encode_charge_acount_response(amount: int, user_id: str):

    to_encode = {"user_id": user_id, "amount": amount}
    try:
        # Encode the JWT token
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    except Exception as e:
        raise ValueError(f"Error creating access token: {str(e)}")

    return encoded_jwt
