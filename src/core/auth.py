import os
import jwt
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from passlib.context import CryptContext  # type: ignore
from src.config import settings

load_dotenv()


class Password:

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def secure_pwd(self, raw_password):
        hashed = self.pwd_context.hash(raw_password)
        return hashed

    def verify_pwd(self, plain, password_hash):
        return self.pwd_context.verify(plain, password_hash)


JWT_ACCESS_TOKEN_EXPIRY_PER_SECOND = int(settings.jwt_access_secs)
JWT_REFRESH_TOKEN_EXPITRY_PER_SECOND = int(settings.jwt_refresh_secs)
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")


def create_access_token(user_id: str, expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            seconds=JWT_ACCESS_TOKEN_EXPIRY_PER_SECOND
        )

    to_encode = {"exp": expires_delta, "user_id": user_id}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str, expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            seconds=JWT_REFRESH_TOKEN_EXPITRY_PER_SECOND
        )

    to_encode = {"exp": expires_delta, "user_id": user_id}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, JWT_ALGORITHM)
    return encoded_jwt


def create_token(user_id):
    output = {
        "access_token": create_access_token(user_id=user_id),
        "refresh_token": create_refresh_token(user_id=user_id),
    }
    return output


def decode_jwt(jwtoken: str):
    try:
        payload = jwt.decode(jwt=jwtoken, options={"verify_signature": False})
        return payload
    except Exception:
        return None


def check_epoch_time(epoch_time):
    if isinstance(epoch_time, str):
        epoch_time = float(epoch_time)
    current_time = time.time()
    return epoch_time > current_time


def refresh_token(refresh_token: str, user_id: str):
    new_access_token = create_access_token(user_id=user_id)
    new_refresh_token = create_refresh_token(user_id=user_id)
    return dict(access_token=new_access_token, refresh_token=new_refresh_token)


def parse_authorization_token(token: str):
    return token.split()[1]
