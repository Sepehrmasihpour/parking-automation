from fastapi import APIRouter, HTTPException, Depends, status
from src.db import user
from src.schemas import user as user_schema
from src.schemas import common as common_schema
from src.core import dependecies
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from src.core import auth as auth_core
from src.config import settings
from bson import ObjectId

router = APIRouter()


def validate_and_sanitize_add_balance_token(token_str: str):
    try:
        # Decode the JWT token using your existing auth_core.decode_jwt function
        payload = auth_core.decode_jwt(token_str)
    except HTTPException as e:
        # Re-raise HTTPException (e.g., token expired, invalid)
        raise e
    except Exception as e:
        # Log the error internally if needed
        # logger.error(f"Token decoding error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error.",
        )

    # Validate expected fields in the payload
    expected_fields = ["user_id", "amount", "exp"]
    for field in expected_fields:
        if field not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing field '{field}' in token payload.",
            )

    # Validate 'user_id' field
    user_id = payload.get("user_id")
    try:
        # Validate that 'user_id' is a valid ObjectId
        user_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 'user_id' format in token payload.",
        )
    payload["user_id"] = user_id

    # Validate 'amount' field
    amount = payload.get("amount")
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 'amount' in token payload.",
        )

    return payload


@router.get("/data", response_model=user_schema.RespGetUser)
async def get_user(user_id=Depends(dependecies.jwt_required)):
    try:

        user_data = await user.get_user_by_id(user_id)
        serialized_data = user_schema.RespGetUser(
            user_name=user_data.get("user_name"),
            balance=user_data.get("balance"),
        )
        return serialized_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal error"
        )


@router.get("/key", response_model=common_schema.Token)
async def get_door_key(user_id=Depends(dependecies.jwt_required)):
    expiry_date = datetime.now() + timedelta(minutes=1)
    to_encode = {"id": user_id, "exp": expiry_date, "type": "user"}
    try:
        encoded_jwt = jwt.encode(
            to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal error"
        )
    return {"token": encoded_jwt}


@router.get("/addBalance/create", response_model=user_schema.RespPostAddBalanceCreate)
async def create_add_balance_token(
    amount: int, user_id=Depends(dependecies.jwt_required)
):
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="no negative numbers"
        )
    expiry_date = datetime.now() + timedelta(minutes=1)
    to_encode = {"exp": expiry_date, "user_id": user_id, "amount": amount}
    try:
        encoded_jwt = jwt.encode(
            to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal error"
        )
    return {"token": encoded_jwt}


@router.post("/addBalance", response_model=common_schema.CommonMessage)
async def pay_add_balance_bill(
    token: common_schema.Token,
    user_is_admin=Depends(dependecies.admin_is_required),
):
    decoded_token = validate_and_sanitize_add_balance_token(token.token)
    user_data = await user.get_user_by_id(decoded_token.get("user_id"))
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no user found with this id found",
        )
    #! here will be the logic for the card reader and if successfull it will call the add balnce encpoint
    payment_successful = True
    if not payment_successful:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="payment failed"
        )
    user_balance = user_data.get("balance")
    await user.update_user_instance(
        decoded_token.get("user_id"),
        {"balance": user_balance + decoded_token.get("amount")},
    )
    return {
        "msg": f"the acount has been charged.\nthis messge will be there if the treansaction is successfull and here we assume that it was successfull"
    }
