import threading
import logging
from datetime import datetime
from apps.services.handle_underlying_blobs import check_underlying_blob_and_move

SCHEDULE_INTERVAL_IN_SECONDS = 5
JOB_NAME = "JOB-HANDLE-UNDERLYING-BLOB"


# function name needs to be job_task for automated picking.
def job_task():
    start_time = datetime.strptime("08:00:00", "%H:%M:%S")
    end_time = datetime.strptime("23:00:00", "%H:%M:%S")
    now = datetime.now().time()

    logging.info(
        "Start - %s, %s - Current date and time : %s",
        threading.current_thread().name,
        JOB_NAME,
        now.strftime("%Y-%m-%d %H:%M:%S"),
    )

    if start_time.time() <= now <= end_time.time():
        logging.info("Running scheduled job...")
        check_underlying_blob_and_move()
        logging.info("Job is finished")
    else:
        print(f"Scheduled job only runs between {start_time.time()} and {end_time.time()}")

    logging.info(
        "Finish - %s, %s - Current date and time : %s",
        threading.current_thread().name,
        JOB_NAME,
        now.strftime("%Y-%m-%d %H:%M:%S"),
    )
