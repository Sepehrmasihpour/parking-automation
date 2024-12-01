from fastapi import APIRouter, HTTPException, Depends, status
from src.db import user, ticket, plan
from src.schemas import user as user_schema
from src.schemas import common as common_schema
from datetime import datetime, timedelta
from src.core import dependecies
from src.core import auth as auth_core
from bson import ObjectId

router = APIRouter()


@router.get("/data", response_model=user_schema.RespGetUser)
async def get_user(user_id=Depends(dependecies.jwt_required)):
    try:

        user_data = await user.get_user_by_id(user_id)
        serialized_data = user_schema.RespGetUser(
            id=auth_core.encode_parking_response(user_data.get("_id")),
            user_name=user_data.get("user_name"),
            passport_id=user_data.get("passport_id"),
            created_at=user_data.get("created_at"),
            balance=user_data.get("balance"),
        )
        return serialized_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/addBalance/issue/{amount}", response_mmodel=common_schema.CommonMessage)
def increase_balance(amount: int, user_id=Depends(dependecies.jwt_required)):
    encoded_payment_action = auth_core.encode_charge_acount_response(
        amount=amount, user_id=user_id
    )
    return {"msg": encoded_payment_action}


@router.post("/addBalance/pay", responde_model=common_schema.CommonMessage)
def pay_add_balance_bill(encoded_bill: str):
    try:
        decoded_bill = auth_core.decode_jwt(encoded_bill)
    except auth_core.JWTDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid bill: {e}"
        )
    user_id = decoded_bill.get("user_id")
    amount = decoded_bill.get("amount")
    #! here will be the logic for the card reader and if successfull it will call the add balnce encpoint
    return {"msg": f"pay {amount} for charging acount"}


@router.post("/addBalance/update", response_model=common_schema.CommonMessage)
async def update_user_balance(
    payload: user_schema.ReqAddBalanceUpdate,
    current_user=Depends(dependecies.jwt_required),
):
    current_user_data = await user.get_user_by_id(current_user)
    user_is_admin = True if current_user_data.get("admin") else False
    if not user_is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="you need to be admin"
        )
    user_current_balance = await user.get_user_by_id(payload.user_id).get("balance")
    await user.update_user_instance(
        payload.user_id, {"balance": user_current_balance + payload.amount}
    )
    return {"msg": f"{payload.amount} added to the user balance"}
