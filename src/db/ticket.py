from src.db import db
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from typing import Union, Optional, Dict
from pymongo.errors import PyMongoError
from datetime import datetime
from fastapi import HTTPException, status


class Ticket(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    expiry_date: datetime
    price: int
    is_paid: bool = False
    used_for_entry: bool = False
    used_for_exit: bool = False
    active: bool = True

    model_config = ConfigDict(arbitrary_types_allowed=True)


async def create_ticket(ticket_data: Ticket):
    try:
        await db.ticket.insert_one(ticket_data.model_dump(by_alias=True))
    except PyMongoError as e:
        print(f"db error:{e}")
        raise
    except Exception as e:
        print(f"error:{e}")
        raise


async def get_ticket_by_id(id: Union[str, ObjectId]):
    try:
        id = ObjectId(id) if isinstance(id, str) else id
        ticket = await db.ticket.find_one({"_id": id})
        return ticket
    except PyMongoError as e:
        print(f"db error:{e}")
        raise
    except Exception as e:
        print(f"error:{e}")
        raise


async def update_ticket_by_id(id: Union[str, ObjectId], update_query: Dict):
    try:
        id = ObjectId(id) if isinstance(id, str) else id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format.",
        )
    try:
        await db.ticket.update_one({"_id": id}, {"$set": update_query})
    except PyMongoError as e:
        print(f"db error:{e}")
        raise
    except Exception as e:
        print(f"error:{e}")
        raise


async def delete_ticket_by_id(id: Union[str, ObjectId]):
    try:
        id = ObjectId(id) if isinstance(id, str) else id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format.",
        )
    try:
        await db.ticket.delete_one({"_id": id})
    except PyMongoError as e:
        print(f"db error:{e}")
        raise
    except Exception as e:
        print(f"error:{e}")
        raise


async def delete_inactive_tickets():
    try:
        await db.ticket.delete_many({"active": False})
        await db.ticket.delete_many({"expiry_date": {"$lt": datetime.datetime.now()}})
    except PyMongoError as e:
        print(f"db error:{e}")
        raise
    except Exception as e:
        print(f"error:{e}")
        raise
