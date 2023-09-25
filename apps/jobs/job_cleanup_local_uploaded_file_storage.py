from datetime import datetime
import logging
import os
import shutil
import threading
import time, stat
from pathlib import Path

from apps.common import config_reader

# every hour
SCHEDULE_INTERVAL_IN_SECONDS = 30
JOB_NAME = "JOB_CLEANUP_LOCAL_UPLOADED_FILE_STORAGE"

MAX_ALLOWED_HOURS = 6


def job_task():
    now = datetime.now()
    now_unix_timestamp = time.mktime(now.timetuple())
    logging.info(
        "Start - %s, thread: %s at %s",
        JOB_NAME,
        threading.current_thread().name,
        now.strftime("%Y-%m-%d %H:%M:%S"),
    )
    # ----------------------------------------------------------------

    local_save_folder = config_reader.config_data.get("Main", "app_base_dir") + "/uploaded_file_storage/"
    local_save_folder_path = Path(local_save_folder).absolute()
    items = os.scandir(local_save_folder_path)
    logging.info("Found %s items in '%s' to scan.", len(list(items)), local_save_folder)

    for item in os.scandir(local_save_folder_path):
        if __should_skip_item(item):
            logging.info("Skipping '%s' as its name matches the ignored items.", item.name)
        else:
            item_stats = item.stat()
            diff = now_unix_timestamp - float(item_stats[stat.ST_MTIME])
            diff_in_hours = 0
            if diff > 0:
                diff_in_hours = diff / (60 * 60)

            if diff_in_hours > MAX_ALLOWED_HOURS:
                logging.info(
                    "Cleaning up '%s' as its last modified time is %s (i.e %.2f hours earlier than now)",
                    item.name,
                    item_stats[stat.ST_MTIME],
                    diff_in_hours,
                )
                __cleanup_item(item)
            else:
                logging.info(
                    "Ignoring '%s' as its last modified time is %s (i.e %.2f hours earlier than now)",
                    item.name,
                    item_stats[stat.ST_MTIME],
                    diff_in_hours,
                )

    # ----------------------------------------------------------------
    logging.info(
        "Finish - %s, thread: %s at %s",
        JOB_NAME,
        threading.current_thread().name,
        now.strftime("%Y-%m-%d %H:%M:%S"),
    )


def __should_skip_item(item: os.DirEntry[str]):
    name = item.name
    ret_val = False
    if (name == ".DS_Store") or (name.startswith("__") or (name.startswith("dummy"))):
        ret_val = True

    return ret_val


def __cleanup_item(item: os.DirEntry[str]):
    if item.is_dir() and not item.is_symlink():
        shutil.rmtree(item.path)
    else:
        os.remove(item.path)
