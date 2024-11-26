from src.db import db
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from typing import Union
from pymongo.errors import PyMongoError
from datetime import datetime, timedelta
from fastapi import HTTPException, status


class Plan(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    expiry_date: datetime
    user_id: ObjectId

    model_config = ConfigDict(arbitrary_types_allowed=True)


async def create_plan(plan_data: Plan):
    try:
        await db.plan.insert_one(plan_data.model_dump(by_alias=True))
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def get_plan_by_id(id: Union[str, ObjectId]):
    try:
        id = ObjectId(id) if isinstance(id, str) else id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format.",
        )
    try:
        plan = await db.plan.find_one({"_id": id})
        return plan
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def get_plan_by_user_id(id: Union[str, ObjectId]):
    try:
        id = ObjectId(id) if isinstance(id, str) else id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format.",
        )
    try:
        plan = await db.plan.find_one({"user_id": id})
        return plan
    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")


async def renew_plan_by_id(id: Union[ObjectId, str], time_to_add: timedelta):
    try:

        try:
            id = ObjectId(id) if isinstance(id, str) else id
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan ID format.",
            )

        # Retrieve the current plan
        plan = await db.plan.find_one({"_id": id})
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No plan found with id {id}",
            )

        current_expiry_date = plan["expiry_date"]
        new_expiry_date = (
            current_expiry_date + time_to_add
            if current_expiry_date < datetime.now()
            else datetime.now() + time_to_add
        )

        # Update the expiry_date in the database
        result = await db.plan.find_one_and_update(
            {"_id": id}, {"$set": {"expiry_date": new_expiry_date}}
        )

        return result

    except PyMongoError as e:
        print(f"db error:{e}")
    except Exception as e:
        print(f"error:{e}")
