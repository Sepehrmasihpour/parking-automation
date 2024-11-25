from src.db import db
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from typing import Union, Dict
from pymongo.errors import PyMongoError
from datetime import datetime


class User(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    user_name: str
    phone_number: str
    validated: bool = False
    passport_id: ObjectId
    created_at: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)


async def create_user(user_data: User):
    try:
        await db.user.insert_one(user_data.model_dump(by_alias=True))
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def get_user_by_user_name(user_name: str):
    try:
        data = await db.user.find_one({"user_name": user_name})
        return data
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def get_user_by_id(id: Union[str, ObjectId]):
    try:

        id = ObjectId(id) if isinstance(id, str) else id
        data = await db.user.find_one({"_id": id})
        return data
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def get_user_by_phone_number(phone_number: str):
    try:
        data = await db.user.find_one({"phone_number": phone_number})
        return data
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def update_user_instance(id: Union[str, ObjectId], update_query: Dict):
    try:
        id = ObjectId(id) if isinstance(id, str) else id
        await db.user.update_one({"_id": id}, {"$set": update_query})
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")
