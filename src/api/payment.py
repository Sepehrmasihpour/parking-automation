from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from src.schema import common as common_schema
from src.db import crud

router = APIRouter()


@router.post("/pay")
async def pay(token_id: int):

    #! Replace this with the actual payment page URL when integrating
    return RedirectResponse(url=f"/payment_callback/{token_id}")


@router.post("/payment_callback", response_model=common_schema.CommonMessage)
async def payment_callback(token_id: int):
    crud.set_paid_status(token_id, True)
    return {"message": "Payment successful"}
