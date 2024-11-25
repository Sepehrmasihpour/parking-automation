from src.db import db
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from typing import Union, Dict
from pymongo.errors import PyMongoError


class Parking(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="-id")
    entry_door_open: bool
    exit_door_open: bool
    capacity_full: bool

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
