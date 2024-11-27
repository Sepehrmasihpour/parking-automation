from src.db import db
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from typing import Union, List, Optional, Dict, Any
from pymongo.errors import PyMongoError
from datetime import datetime
from fastapi import HTTPException, status


class Ticket(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    expiry_date: datetime
    user_id: Optional[ObjectId] = None
    parking_id: ObjectId
    price: Optional[int] = None
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
    except Exception as e:
        print(f"error:{e}")


async def get_usable_ticket_by_user_id(id: Union[str, ObjectId], skip: int, limit: int):
    try:
        id = ObjectId(id) if isinstance(id, str) else id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format.",
        )
    try:
        current_time = datetime.now()
        data = (
            db.ticket.find(
                {"user_id": id, "active": True, "expiry_date": {"$gt": current_time}}
            )
            .skip(skip)
            .limit(limit)
        )
        return await data.to_list(length=None)

    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


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
    except Exception as e:
        print(f"error:{e}")


async def get_ticket_count(query: Dict[str, Any]) -> int:
    document_count = await db.ticket.count_documents(query)
    return document_count
