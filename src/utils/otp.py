import pyotp
from src.db import redis_client as redis
from bson import ObjectId
from src.db import auth, user
from typing import Union


async def generate_otp(user_id: Union[str, ObjectId]):
    user_data = await user.get_user_by_id(id=user_id)
    auth_passport_id = user_data.get("passport_id")
    auth_passport = await auth.get_auth_passport_by_id(
        auth_passport_id=auth_passport_id
    )
    otp_secret = auth_passport.get("otp_secret")

    # Initialize the TOTP client using the secret
    otp_client = pyotp.TOTP(otp_secret, interval=120)

    # Generate the OTP token
    otp_token = otp_client.now()

    return otp_token


async def validate_otp(otp_token: str, user_id: Union[str, ObjectId]):

    # Retrieve the user's data and the auth passport to get the OTP secret
    user_data = await user.get_user_by_id(id=user_id)
    auth_passport_id = user_data.get("passport_id")
    auth_passport = await auth.get_auth_passport_by_id(
        auth_passport_id=auth_passport_id
    )
    otp_secret = auth_passport.get("otp_secret")

    # Initialize the TOTP client using the secret
    otp_client = pyotp.TOTP(otp_secret, interval=120)

    # Validate the OTP using pyotp
    if not otp_client.verify(otp_token):
        return False  # OTP is invalid based on pyotp verification

    return True  # OTP is successfully validated
