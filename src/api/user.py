from fastapi import APIRouter, HTTPException, Depends, status
from src.db import user
from src.schemas import user as user_schema
from src.schemas import common as common_schema
from src.core import dependecies
from src.core import auth as auth_core

router = APIRouter()


@router.get("/data", response_model=user_schema.RespGetUser)
async def get_user(user_id=Depends(dependecies.jwt_required)):
    try:

        user_data = await user.get_user_by_id(user_id)
        serialized_data = user_schema.RespGetUser(
            id=str(user_data.get("_id")),
            user_name=user_data.get("user_name"),
            balance=user_data.get("balance"),
        )
        return serialized_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/addBalance/issue", response_model=common_schema.CommonMessage)
async def pay_add_balance_bill(payload: user_schema.ReqPostAddBalanceIssue):
    user_data = await user.get_user_by_id(payload.user_id)
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
        payload.user_id, {"balance": user_balance + payload.amount}
    )
    return {
        "msg": f"the acount with the user_id of {payload.user_id} has been charged with the amount of {payload.amount}.\nthis messge will be there if the treansaction is successfull and here we assume that it was successfull"
    }
