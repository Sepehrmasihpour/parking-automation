from dotenv import load_dotenv
from urllib.parse import quote_plus
from os import getenv
import multiprocessing

load_dotenv()


class Settings:

    db_uri = getenv("DB_URI")
    db_name = getenv("DB_NAME")

    # * The code for the jwt auth
    jwt_secret = getenv("JWT_SECRET_KEY")
    jwt_access_hours = int(getenv("JWT_ACCESS_HOURS"))
    jwt_refresh_hours = int(getenv("JWT_REFRESH_HOURS"))
    jwt_algorithm = getenv("JWT_ALGORITHM")

    # * the config for the app itself
    webserver_port = getenv("WEBSERVER_PORT")
    webserver_host = getenv("WEBSERVER_HOST")
    worker_count = multiprocessing.cpu_count() * 2 + 1
    broker_uri = getenv("BROKER_URI")

    # * config for the sms service
    sms_service_api_key = getenv("SMS_SERVICE_API_KEY")

    # * config for the reddis db
    redis_url = getenv("REDIS_URL")


settings = Settings()
