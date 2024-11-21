import threading
import schedule
import time
from db import crud  # Assuming you have this function in your db module


# Function to run the scheduler
def run_scheduler():
    schedule.every().day.at("00:00").do(crud.cleanse_db)
    while True:
        schedule.run_pending()
        time.sleep(60)


# Start the scheduler in a separate thread
def start_scheduler():
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
