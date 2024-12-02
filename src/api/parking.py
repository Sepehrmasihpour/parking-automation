from fastapi import APIRouter, HTTPException, status
from src.db import ticket, user
from src.schemas import parking as parking_schema
from src.schemas import common as common_schema
from datetime import datetime, timedelta
from src.config import settings
from typing import Literal

router = APIRouter()


@router.post("/ticket", response_model=parking_schema.RespPostTicket)
async def create_ticket():
    try:

        parking_price = settings.parking_price
        ticket_data = ticket.Ticket(
            expiry_date=datetime.now().timestamp()
            + timedelta(
                minutes=30
            ),  #! After payment this should change to 24 hours or something
            price=parking_price,
        )
        await ticket.create_ticket(ticket_data)
        ticket_id = ticket_data.id
        return {"ticket_id": str(ticket_id)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/ticket/updateExpiry", response_model=common_schema.CommonMessage)
async def update_ticket_expiry(payload: parking_schema.ReqPostTicketUpdateExpiry):
    try:
        await ticket.update_ticket_by_id(
            payload.ticket_id, {"expiry_date": payload.expiry_date}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/open/{door}", response_model=common_schema.CommonMessage)
async def enter_parking(
    door: Literal["entery", "exit"], payload: parking_schema.ReqPostEnterExit
):
    user_id_present = payload.type == "user"
    ticket_id_present = payload.type == "ticket"

    if ticket_id_present:
        ticket_data = await ticket.get_ticket_by_id(payload.id)
        if ticket_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No ticket with this ID was found.",
            )

        if not ticket_data.get("active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="this ticket is inactive"
            )

        ticket_expiry_date = ticket_data.get("expiry_date")
        if ticket_expiry_date < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The expiry date for the ticket has passed.",
            )
        is_used = (
            ticket_data.get("used_for_entry")
            if door == "entery"
            else ticket_data.get("used_for_exit")
        )
        if is_used:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already used this ticket for entry.",
            )
        if not ticket_data.get("is_paid"):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Payment required: {ticket_data.get('price')}",
            )  #! after the payment is confirmed we will update the ticket expiry time to 12 hours
        await ticket.update_ticket_by_id(
            id=payload.id,
            update_query=(
                {"used_for_entry": True}
                if door == "entery"
                else {"used_for_exit": True, "active": False}
            ),
        )

        return {"msg": f"Open {door} gate for guest"}

    if user_id_present:
        user_data = await user.get_user_by_id(payload.id)
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user with this ID was found.",
            )
        if door == "entery":

            user_balance = user_data.get("balance")
            if user_balance is None or user_balance < settings.parking_price:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Payment required: {ticket_data.get('price')}",
                )
            await user.update_user_instance(
                payload.id,
                {
                    "balance": user_balance - settings.parking_price,
                    "last_enterd": datetime.now(),
                },
            )
            return {"msg": f"Open {door} gate for user"}
        else:
            last_entered = user_data.get("last_enterd")
            if last_entered is None:
                # User has never entered
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Payment required: User has not entered in the last 12 hours.",
                )

            time_since_last_entered = datetime.now() - last_entered
            if time_since_last_entered > timedelta(hours=12):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Payment required: User's entry is older than 12 hours.",
                )

            return {"msg": f"Open {door} gate for user"}
