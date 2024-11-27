from fastapi import APIRouter, HTTPException, Depends, status
from src.db import user, ticket, plan
from src.schemas import user as user_schema
from src.schemas import common as common_schema
from datetime import datetime, timedelta
from src.core import dependecies
from bson import ObjectId
from src.utils import pagination

router = APIRouter()


@router.get("/status", response_model=user_schema.RespGetUser)
async def get_user(user_id=Depends(dependecies.jwt_required)):
    try:

        user_data = await user.get_user_by_id(user_id)
        serialized_data = user_schema.RespGetUser(
            id=user_data.get("_id"),
            user_name=user_data.get("user_name"),
            phone_number=user_data.get("phone_number"),
            validated=user_data.get("validated"),
            passport_id=user_data.get("passport_id"),
            parking_history_id=user_data.get("parking_history_id"),
            created_at=user_data.get("created_at"),
        )
        return serialized_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/tickets", response_model=pagination.PaginatedResponse)
async def get_user_tickets(
    page_params: pagination.PaginationParams, user_id=Depends(dependecies.jwt_required)
):
    try:

        tickets = await ticket.get_usable_ticket_by_user_id(
            id=user_id, limit=page_params.per_page, skip=page_params.page
        )
        document_count = await ticket.get_ticket_count(
            {
                "user_id": ObjectId(user_id),
                "active": True,
                "expiry_date": {"$gt": datetime.now()},
            }
        )
        page = pagination.paginate(
            paginated_items=tickets, pagination_params=page_params, total=document_count
        )
        return page
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/plan", response_model=user_schema.RespGetPlan)
async def get_user_plan(user_id=Depends(dependecies.jwt_required)):
    user_plan = await plan.get_plan_by_user_id(id=user_id)
    if user_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no plan with this user_id found",
        )
    serialized_plan = user_schema.RespGetPlan(
        id=str(user_plan.get("_id")),
        expiry_date=user_plan.get("expiry_date"),
        user_id=user_id,
    )
    return serialized_plan
