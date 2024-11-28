import jwt
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

# Environment Variables
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_ACCESS_TOKEN_EXPIRY_PER_SECOND = int(os.getenv("JWT_ACCESS_SECS", 300))
JWT_REFRESH_TOKEN_EXPITRY_PER_SECOND = int(os.getenv("JWT_REFRESH_SECS", 600))


def create_access_token(user_id: str, expires_delta: int = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRY_PER_SECOND)
    elif isinstance(expires_delta, int):
        expires_delta = timedelta(seconds=expires_delta)

    to_encode = {"exp": datetime.utcnow() + expires_delta, "user_id": user_id}
    encoded_jwt = jwt.encode(to_encode, key=JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_jwt(jwtoken: str):
    try:
        payload = jwt.decode(jwt=jwtoken, key=JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def parse_authorization_token(token: str):
    parts = token.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Invalid token format")
    return parts[1]
