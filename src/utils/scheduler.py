import threading
import schedule
import time
from src.db import crud


def run_scheduler():
    schedule.every().day.at("00:00").do(crud.cleanse_db)
    while True:
        schedule.run_pending()
        time.sleep(60)


def start_scheduler():
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
