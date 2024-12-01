from fastapi import APIRouter, HTTPException, status
from src.db import ticket, user
from src.schemas import parking as parking_schema
from src.schemas import common as common_schema
from datetime import datetime, timedelta
from src.core import auth as auth_core
from src.config import settings

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
        return {
            "ticket_id": auth_core.encode_parking_response(ticket_id=str(ticket_id))
        }
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


@router.post("/enter", response_model=common_schema.CommonMessage)
async def enter_parking(payload: parking_schema.ReqPostEnterExit):
    try:
        decoded_id = auth_core.decode_jwt(payload.id)
    except auth_core.JWTDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid ID: {e}"
        )

    user_id_present = decoded_id.get("user_id") is not None
    ticket_id_present = decoded_id.get("ticket_id") is not None

    if user_id_present == ticket_id_present:
        # Both are present or both are absent
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format: must contain either 'user_id' or 'ticket_id', but not both.",
        )

    if ticket_id_present:
        ticket_data = await ticket.get_ticket_by_id(decoded_id.get("ticket_id"))
        if ticket_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No ticket with this ID was found.",
            )

        ticket_expiry_date = ticket_data.get("expiry_date")
        if ticket_expiry_date < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The expiry date for the ticket has passed.",
            )
        if ticket_data.get("used_for_entry"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already used this ticket for entry.",
            )
        if not ticket_data.get("is_paid"):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Payment required: {ticket_data.get('price')}",
            )
        await ticket.update_ticket_by_id(
            id=decoded_id.get("ticket_id"), update_query={"used_for_entry": True}
        )
        return {"msg": "Open entry gate for guest"}

    if user_id_present:
        user_data = await user.get_user_by_id(decoded_id.get("user_id"))
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user with this ID was found.",
            )
        user_balance = user_data.get("balance")
        if user_balance is None or user_balance < settings.parking_price:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough balance."
            )
        await user.update_user_instance(
            decoded_id.get("user_id"),
            {"balance": user_balance - settings.parking_price},
        )
        return {"msg": "Open entry gate for user"}


@router.post("/exit", response_model=common_schema.CommonMessage)
async def exit_parking(payload: parking_schema.ReqPostEnterExit):
    try:
        decoded_id = auth_core.decode_jwt(payload.id)
    except auth_core.JWTDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid ID: {e}"
        )

    user_id_present = decoded_id.get("user_id") is not None
    ticket_id_present = decoded_id.get("ticket_id") is not None

    if user_id_present == ticket_id_present:
        # Both are present or both are absent
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format: must contain either 'user_id' or 'ticket_id', but not both.",
        )

    if ticket_id_present:
        ticket_data = await ticket.get_ticket_by_id(decoded_id.get("ticket_id"))
        if ticket_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No ticket with this ID was found.",
            )

        ticket_expiry_date = ticket_data.get("expiry_date")
        if ticket_expiry_date < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The expiry date for the ticket has passed.",
            )
        if ticket_data.get("used_for_exit"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already used this ticket for exit.",
            )

        await ticket.update_ticket_by_id(
            id=decoded_id.get("ticket_id"),
            update_query={"used_for_exit": True, "active": False},
        )
        return {"msg": "Open exit gate for guest"}

    if user_id_present:
        user_data = await user.get_user_by_id(decoded_id.get("user_id"))
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user with this ID was found.",
            )

        return {"msg": "Open exit gate for user"}
