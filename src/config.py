from dotenv import load_dotenv
from os import getenv
import multiprocessing

load_dotenv()


class Settings:
    price = getenv("PARKING_PRICE")


settings = Settings()
