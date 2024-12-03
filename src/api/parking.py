from fastapi import APIRouter, HTTPException, status, Depends
from src.db import ticket, user
from src.schemas import parking as parking_schema
from src.schemas import common as common_schema
from datetime import datetime, timedelta
from src.config import settings
from typing import Literal, Optional
from src.core import dependecies
from src.core import auth as auth_core
from src.config import settings
import jwt
from bson import ObjectId

router = APIRouter()


def validate_and_sanitize_token(token_str: str):

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
    expected_fields = ["type", "id", "exp"]
    for field in expected_fields:
        if field not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing field '{field}' in token payload.",
            )

    # Validate 'type' field
    token_type = payload.get("type")
    if token_type not in ["user", "ticket"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type."
        )

    # Validate 'id' field
    token_id = payload.get("id")
    try:
        # Validate that 'id' is a valid ObjectId
        token_id = ObjectId(token_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 'id' format in token payload.",
        )

    # Replace 'id' in payload with the ObjectId instance
    payload["id"] = token_id

    return payload


@router.post("/ticket", response_model=parking_schema.RespPostTicket)
async def create_ticket():
    try:

        parking_price = settings.parking_price
        ticket_data = ticket.Ticket(
            expiry_date=datetime.now()
            + timedelta(
                minutes=30
            ),  #! After payment this should change to 24 hours or something
            price=parking_price,
        )
        await ticket.create_ticket(ticket_data)
        ticket_id = ticket_data.id
        token_expiry_date = datetime.now() + timedelta(hours=12)
        to_encode = {
            "exp": token_expiry_date,
            "id": str(ticket_id),
            "type": "ticket",
        }
        try:
            encoded_jwt = jwt.encode(
                to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="failed to encode the token",
            )
        return {"token": encoded_jwt}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="internal server error",
        )


@router.post("/open/{door}", response_model=common_schema.CommonMessage)
async def enter_parking(
    door: Literal["entry", "exit"],
    token: common_schema.Token,
    user_is_admin=Depends(dependecies.jwt_required),
    payment_successfull: Optional[bool] = None,
):
    decoded_token = validate_and_sanitize_token(token.token)
    user_id_present = decoded_token.get("type") == "user"
    ticket_id_present = decoded_token.get("type") == "ticket"

    if ticket_id_present:
        ticket_data = await ticket.get_ticket_by_id(decoded_token.get("id"))
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
            if door == "entry"
            else ticket_data.get("used_for_exit")
        )
        if is_used:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already used this ticket for entry.",
            )
        if not ticket_data.get("is_paid"):
            if payment_successfull is not None and payment_successfull:
                new_expiry_date = datetime.now() + timedelta(hours=12)
                await ticket.update_ticket_by_id(
                    decoded_token.get("id"),
                    {"expiry_date": new_expiry_date, "is_paid": True},
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Payment required: {ticket_data.get('price')}",
                )  #! after the payment is confirmed we will update the ticket expiry time to 12 hours
        await ticket.update_ticket_by_id(
            id=decoded_token.get("id"),
            update_query=(
                {"used_for_entry": True}
                if door == "entry"
                else {"used_for_exit": True, "active": False}
            ),
        )

        return {"msg": f"Open {door} gate for guest"}

    if user_id_present:
        user_data = await user.get_user_by_id(decoded_token.get("id"))
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user with this ID was found.",
            )
        if door == "entry":

            user_balance = user_data.get("balance")
            if user_balance is None or user_balance < settings.parking_price:
                if payment_successfull is not None and payment_successfull:
                    pass
                else:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail=f"Payment required: {ticket_data.get('price')}",
                    )
            await user.update_user_instance(
                decoded_token.get("id"),
                {
                    "balance": user_balance - settings.parking_price,
                    "last_enterd": datetime.now(),
                },
            )
            return {"msg": f"Open {door} gate for user"}
        else:
            last_entered = user_data.get("last_enterd")
            if last_entered is None:
                user_balance = user_data.get("balance")
                if user_balance is None or user_balance < settings.parking_price:
                    if payment_successfull is not None and payment_successfull:
                        pass
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_402_PAYMENT_REQUIRED,
                            detail=f"Payment required: {ticket_data.get('price')}",
                        )
                await user.update_user_instance(
                    decoded_token.get("id"),
                    {
                        "balance": user_balance - settings.parking_price,
                        "last_enterd": datetime.now(),
                    },
                )
                return {"msg": f"Open {door} gate for user"}

            time_since_last_entered = datetime.now() - last_entered
            if time_since_last_entered > timedelta(hours=12):
                user_balance = user_data.get("balance")
                if user_balance is None or user_balance < settings.parking_price:
                    if payment_successfull is not None and payment_successfull:
                        pass
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_402_PAYMENT_REQUIRED,
                            detail=f"Payment required: {ticket_data.get('price')}",
                        )
                await user.update_user_instance(
                    decoded_token.get("id"),
                    {
                        "balance": user_balance - settings.parking_price,
                        "last_enterd": datetime.now(),
                    },
                )

            return {"msg": f"Open {door} gate for user"}
