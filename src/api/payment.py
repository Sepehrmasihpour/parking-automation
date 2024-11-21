from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from src.schema import common as common_schema
from src.db import crud

router = APIRouter()


# Endpoint that simulates redirecting to the external payment page
@router.post("/pay")
async def pay(token_id: int):
    # In a real scenario, redirect to the external payment service
    # Replace this with the actual payment page URL when integrating
    return RedirectResponse(url=f"/payment_callback/{token_id}")


# Endpoint that the payment service calls upon successful payment
@router.post("/payment_callback", response_model=common_schema.CommonMessage)
async def payment_callback(token_id: int):
    crud.set_paid_status(token_id, True)
    return {"message": "Payment successful"}
