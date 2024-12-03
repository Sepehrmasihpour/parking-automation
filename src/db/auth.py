from src.db import db
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from typing import Union, List, Optional
from pymongo.errors import PyMongoError


class Auth(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    user_id: ObjectId = Field()
    password_repository: List[Union[str, None]]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AuthPassport(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    password_hash: Optional[str] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)


async def create_auth(user_id: Union[ObjectId, str]):
    try:
        user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        auth_instance = Auth(user_id=user_id, password_repository=[])
        await db.auth.insert_one(auth_instance.model_dump(by_alias=True))
    except PyMongoError as e:
        print(f"db error:{e}")
        raise
    except Exception as e:
        print(f"error:{e}")
        raise


async def create_auth_passport(auth_passport: AuthPassport):
    try:
        await db.auth_passport.insert_one(auth_passport.model_dump(by_alias=True))
    except PyMongoError as e:
        print(f"db error:{e}")
        raise
    except Exception as e:
        print(f"error:{e}")
        raise


async def update_new_password(
    password_hash: str,
    passport_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
):
    try:

        user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        passport_id = (
            ObjectId(passport_id) if isinstance(passport_id, str) else passport_id
        )

        await db.auth_passport.find_one_and_update(
            {"_id": passport_id}, {"$set": {"password_hash": password_hash}}
        )

        await db.auth.find_one_and_update(
            {"user_id": user_id},
            {"$push": {"password_repository": password_hash}},
        )
    except PyMongoError as e:
        print(f"db error:{e}")
        raise
    except Exception as e:
        print(f"error:{e}")
        raise


async def get_auth_passport_by_id(auth_passport_id: Union[ObjectId, str]):
    try:

        auth_passport_id = (
            ObjectId(auth_passport_id)
            if isinstance(auth_passport_id, str)
            else auth_passport_id
        )
        data = await db.auth_passport.find_one({"_id": auth_passport_id})
        return data
    except PyMongoError as e:
        print(f"db error:{e}")
        raise
    except Exception as e:
        print(f"error:{e}")
        raise
