from fastapi import APIRouter, HTTPException
from utils import qr_code
from db import crud
from schema import common as common_schema

router = APIRouter()


# Endpoint to create a new parking token and generate QR code
@router.post("/create_token", response_model=common_schema.CommonMessage)
async def create_token():

    token_id = crud.create_parking_token()
    qr_filename = qr_code.generate_payment_qr(token_id)
    return {
        "message": f"Parking token created with ID {token_id}. QR code saved as {qr_filename}."
    }


@router.get("/check/{token_id}")
async def check_status(token_id: int):
    is_paid = crud.get_paid_status(token_id)
    if is_paid is not None:
        return {"token_id": token_id, "is_paid": bool(is_paid)}
    else:
        raise HTTPException(status_code=404, detail="Token not found")
