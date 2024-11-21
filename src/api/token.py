from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.utils import qr_code
from src.db import crud
from src.schema import common as common_schema

router = APIRouter()


@router.post("/create")
async def create_token():
    token_id = crud.create_parking_token()
    img_byte_arr = qr_code.generate_payment_qr(token_id)
    headers = {"Content-Disposition": f'attachment; filename="qrcode_{token_id}.png"'}
    return StreamingResponse(img_byte_arr, media_type="image/png", headers=headers)


@router.get("/check/{token_id}")
async def check_status(token_id: int):
    is_paid = crud.get_paid_status(token_id)
    if is_paid is not None:
        return {"token_id": token_id, "is_paid": bool(is_paid)}
    else:
        raise HTTPException(status_code=404, detail="Token not found")
