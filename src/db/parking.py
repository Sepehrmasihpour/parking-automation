from src.db import db
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from typing import Union, Dict, List, Optional
from pymongo.errors import PyMongoError


class Parking(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="-id")
    name: str
    entry_door_open: bool = False
    price: int
    exit_door_open: bool = False
    capacity_full: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ParkingHistory(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="-id")
    parking_history: Optional[List[ObjectId]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


async def create_parking_instance(parking_data: Parking):
    try:
        await db.parking.insert_one(parking_data.model_dump(by_alias=True))
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def change_Parking_status_by_id(id: Union[str, ObjectId], update_query: Dict):
    try:
        id = ObjectId(id) if isinstance(id, str) else id
        data = await db.parking.find_one_and_update(
            filter={"_id": id}, update={"$set": update_query}
        )
        return data
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def get_parking_by_id(id: Union[str, ObjectId]):
    try:
        id = ObjectId(id) if isinstance(id, str) else id
        data = await db.parking.find_one({"_id": id})
        return data
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def create_parking_history_instance(instance: ParkingHistory):
    try:
        await db.parking_history.insert_one(instance.model_dump(by_alias=True))
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def get_parking_history_by_id(id: Union[str, ObjectId]):
    try:
        data = await db.parking_history.find_one({"_id": id})
        return data
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def add_parking_to_parking_history(
    id: Union[str, ObjectId], parking_id: Union[str, ObjectId]
):
    try:
        parking_id = ObjectId(parking_id) if isinstance(parking_id, str) else parking_id
        id = ObjectId(id) if isinstance(id, str) else id
        parking_history = await db.parking_history.find_one({"_id": id})
        history_list = parking_history.get("parking_history", [])
        history_list = [pid for pid in history_list if pid != parking_id]
        history_list.append(parking_id)
        await db.parking_history.update_one(
            {"_id": id}, {"$set": {"parking_history": history_list}}
        )
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")
