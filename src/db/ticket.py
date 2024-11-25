from src.db import db
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from typing import Union, List, Optional
from pymongo.errors import PyMongoError
from datetime import datetime
from fastapi import HTTPException, status


class Ticket(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    expiry_date: datetime
    user_id: ObjectId
    parking_id: ObjectId


async def create_ticket(ticket_data: Ticket):
    try:
        await db.ticket.insert_one(ticket_data.model_dump(by_alias=True))
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def get_ticket_by_id(id: Union[str, ObjectId]):
    try:
        id = ObjectId(id) if isinstance(id, str) else id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format.",
        )
    try:
        ticket = await db.ticket.find_one({"_id": id})
        return ticket
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")
