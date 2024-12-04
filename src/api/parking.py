from fastapi import APIRouter, HTTPException, status, Depends, Request
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
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="templates")


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


@router.get("/ticket", response_class=HTMLResponse)
async def create_ticket(request: Request):
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
        return templates.TemplateResponse(
            "ticket.html", {"request": request, "token": encoded_jwt}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"internal server error:{str(e)}",
        )


@router.post("/open/{door}", response_model=common_schema.CommonMessage)
async def enter_parking(
    door: Literal["entry", "exit"],
    token: common_schema.Token,
    user_is_admin=Depends(dependecies.jwt_required),
    payment_successfull: Optional[bool] = None,
):
    decoded_token = validate_and_sanitize_token(token.token)
    token_type = decoded_token.get("type")
    token_id = decoded_token.get("id")

    if token_type == "ticket":
        # Process ticket logic
        ticket_data = await ticket.get_ticket_by_id(token_id)
        if not ticket_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No ticket with this ID was found.",
            )
        if not ticket_data.get("active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This ticket is inactive.",
            )
        if ticket_data.get("expiry_date") < datetime.now():
            await ticket.update_ticket_by_id(token_id, {"active": False})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The expiry date for the ticket has passed.",
            )
        is_used_key = "used_for_entry" if door == "entry" else "used_for_exit"
        if ticket_data.get(is_used_key):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You have already used this ticket for {door}.",
            )
        if not ticket_data.get("is_paid"):
            if payment_successfull:
                new_expiry_date = datetime.now() + timedelta(hours=12)
                await ticket.update_ticket_by_id(
                    token_id,
                    {"expiry_date": new_expiry_date, "is_paid": True},
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Payment required: {ticket_data.get('price')}",
                )
        await ticket.update_ticket_by_id(
            token_id,
            {
                is_used_key: True,
                **({"active": False} if door == "exit" else {}),
            },
        )
        return {"msg": f"Open {door} gate for guest without pay(demo)"}

    elif token_type == "user":
        # Process user logic
        user_data = await user.get_user_by_id(token_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user with this ID was found.",
            )
        user_balance = user_data.get("balance")
        if door == "entry":
            if user_balance < settings.parking_price:
                if payment_successfull:
                    await user.update_user_instance(
                        token_id,
                        {
                            "balance": 0,
                            "last_entered": datetime.now(),
                        },
                    )
                    return {
                        "msg": f"Open {door} gate for user with not enough funds(demo)"
                    }
                else:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail=f"Payment required: {settings.parking_price}",
                    )
            else:
                new_balance = user_balance - settings.parking_price
                await user.update_user_instance(
                    token_id,
                    {
                        "balance": new_balance,
                        "last_entered": datetime.now(),
                    },
                )
            return {"msg": f"Open {door} gate for user"}

        elif door == "exit":
            last_entered = user_data.get("last_entered")
            if not last_entered or (datetime.now() - last_entered) > timedelta(
                hours=12
            ):
                # Need to charge for exit if no entry recorded or parking time exceeded
                if user_balance < settings.parking_price:
                    if payment_successfull:
                        await user.update_user_instance(
                            token_id,
                            {"balance": 0},
                        )
                        return {"msg": f"Open {door} gate for user (demo)"}
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_402_PAYMENT_REQUIRED,
                            detail=f"Payment required: {settings.parking_price}",
                        )
                else:
                    new_balance = user_balance - settings.parking_price
                    await user.update_user_instance(
                        token_id,
                        {"balance": new_balance},
                    )
            # No additional charge if within parking time
            return {"msg": f"Open {door} gate for user"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type.",
        )
