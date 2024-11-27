from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
    OAuth2PasswordBearer,
)
from src.core import auth
from src.db import redis_client, user

# Define the security scheme
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/password")


async def jwt_required(token: str = Depends(oauth2_scheme)):
    access_token = token

    # Check if token is blacklisted
    is_blacklisted = redis_client.get(access_token)
    if is_blacklisted:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    decoded = auth.decode_jwt(jwtoken=access_token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = decoded.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


async def user_is_validated(user_id=Depends(jwt_required)):
    user_data = await user.get_user_by_id(id=user_id)
    user_is_validated = True if user_data.get("validated") else False
    if not user_is_validated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="this user is not validated",
        )
    return user_id


async def get_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    access_token = credentials.credentials

    # Optionally, add validation for token format
    if not access_token:
        raise HTTPException(status_code=401, detail="Authorization token is missing")

    return access_token
