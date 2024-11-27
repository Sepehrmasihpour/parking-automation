from fastapi import APIRouter, HTTPException, Depends, status
from src.db import parking, ticket, plan
from src.schemas import parking as parking_schema
from src.schemas import common as common_schema
from datetime import datetime, timedelta
from src.core import dependecies

router = APIRouter()


@router.post("/ticket", response_model=parking_schema.RespPostTicket)
async def create_ticket(
    parking_id: str, user_id=Depends(dependecies.user_is_validated)
):
    user_plan = await plan.get_plan_by_user_id(id=user_id)
    if user_plan is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You do not have any plan"
        )
    plan_is_expired = True if user_plan.get("expiry_date") < datetime.now() else False

    if plan_is_expired:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="your plan has expired"
        )
    ticket_data = ticket.Ticket(
        expiry_date=datetime.now() + timedelta(hours=24),
        user_id=user_id,
        parking_id=parking_id,
    )
    await ticket.create_ticket(ticket_data)
    ticket_id = ticket_data.id
    return {"ticket_id": str(ticket_id)}


@router.post("/enter", response_model=common_schema.CommonMessage)
async def enter_parking(payload: parking_schema.ReqPostEnterExit):
    ticket_data = await ticket.get_ticket_by_id(payload.ticket_id)
    if ticket_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ticket with this id was found",
        )
    ticket_parking_id = ticket_data.get("parking_id")
    if not str(ticket_parking_id) == str(payload.parking_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="this ticket is not for this parking",
        )

    ticket_expiry_date = ticket_data.get("expiry_date")
    if ticket_expiry_date < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="the expiry date for the ticket has passed",
        )
    if ticket.get("used_for_entry"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already used this ticket for entry",
        )
    # * The logic for opening the gate goes here
    await ticket.update_ticket_by_id(
        id=payload.ticket_id, update_query={"used_for_entry": True}
    )

    return {"msg": "the gate opened"}


@router.post("/exit", response_model=common_schema.CommonMessage)
async def enter_parking(payload: parking_schema.ReqPostEnterExit):
    ticket_data = await ticket.get_ticket_by_id(payload.ticket_id)
    if ticket_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ticket with this id was found",
        )
    ticket_parking_id = ticket_data.get("parking_id")
    if not str(ticket_parking_id) == str(payload.parking_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="this ticket is not for this parking",
        )

    ticket_expiry_date = ticket_data.get("expiry_date")
    if ticket_expiry_date < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="the expiry date for the ticket has passed",
        )
    if ticket.get("used_for_exit"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already used this ticket for entry",
        )
    # * The logic for closing the gate goes here

    await ticket.update_ticket_by_id(
        id=payload.ticket_id, update_query={"used_for_exit": True}
    )

    return {"msg": "the gate opened"}
