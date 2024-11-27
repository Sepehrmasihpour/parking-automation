from fastapi import APIRouter, HTTPException, Depends, status
from src.db import user, plan
from src.schemas import plan as plan_schema
from src.schemas import common as common_schema
from datetime import datetime, timedelta
from src.core import dependecies
from bson import ObjectId

router = APIRouter()


@router.post("/create", response_model=common_schema.CommonMessage)
async def create_plan(
    expiry_date: datetime, user_id=Depends(dependecies.user_is_validated)
):
    user_has_plan = (
        True if await plan.get_plan_by_user_id(id=user_id) is not None else False
    )
    if user_has_plan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There is already a plan assigned to this user id",
        )
    # * Payment code goes here
    plan_data = plan.Plan(expiry_date=expiry_date, user_id=ObjectId(user_id))
    await plan.create_plan(plan_data)
    return {"msg": "the plan has been created"}


@router.post("/renew", response_model=common_schema.CommonMessage)
async def renew_plan(time_to_add: datetime, user_id=Depends(dependecies.jwt_required)):
    user_plan = await plan.get_plan_by_user_id(id=user_id)
    if user_plan is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="you do not have a plan"
        )
    user_plan_id = user_plan.get("_id")
    await plan.renew_plan_by_id(id=user_plan_id, time_to_add=time_to_add)
    return {"msg": "the plan has been renewed"}
