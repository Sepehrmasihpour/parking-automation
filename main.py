# main.py

from fastapi import FastAPI
import uvicorn
from src.utils import scheduler
from src.api import token, payment

app = FastAPI()

# Include the routers from different route modules
app.include_router(token.router, prefix="/token", tags=["Parking token"])
app.include_router(payment.router, prefix="/payment", tags=["Payment"])

if __name__ == "__main__":
    scheduler.start_scheduler()
    uvicorn.run(app, host="0.0.0.0", port=8000)
