from src.config import Settings as settings
import motor.motor_asyncio
import redis.asyncio as redis

db = motor.motor_asyncio.AsyncIOMotorClient(settings.db_uri).get_database(
    settings.db_name
)
redis_client = redis.from_url(settings.redis_url)
