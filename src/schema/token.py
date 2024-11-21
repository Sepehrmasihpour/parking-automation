from pydantic import BaseModel


class ReqPaymentPay(BaseModel):
    token_id: int
