# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import getopt
import os
import logging
import sys

import dotenv
from apps.common import logging_config, constants, config_reader

# --------------------------------------------------
# STEP 1: Load the logging and config reader before anything else
app_base_dir = os.path.abspath(os.path.dirname(__file__))
logging_config.configure_logging(os.path.abspath(constants.DEFAULT_LOG_FILE_PATH))

# --------------------------------------------------
# STEP 2: reads cmd line args to infer env
app_env = os.environ.get("APP_ENV")
if not app_env:
    app_env = "local"
    logging.warning("No APP_ENV env variable found. Defaulting to 'local'")
else:
    logging.info("APP_ENV inferred from environment variable as %s", app_env)

# --------------------------------------------------
# STEP 3: load the .env file for this env and read app config
dot_env_file_path = app_base_dir + "/config-files/" + app_env + "/.env"
dotenv.load_dotenv(dot_env_file_path)
config_reader.read_config(app_env, app_base_dir)

# --------------------------------------------------
# STEP 4: bootstrap the app and continue further now
from flask_minify import Minify
from sys import exit
from apps.flask_config import config_dict
from apps import create_app

# The configuration
get_config_mode = "Local"
if app_env.lower() == "production":
    get_config_mode = "Production"

try:
    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    exit("Error: Invalid <config_mode>. Expected values [Debug, Production] ")

app = create_app(app_config)

if get_config_mode != "Local":
    Minify(app=app, html=True, js=False, cssless=False)

logging.info("App base directory: %s", app_base_dir)
logging.info("App Env: %s", config_reader.config_data.get("Main", "env"))
logging.info("Flask Debug Mode: %s", str(app_config.DEBUG))
logging.info("Flask Page Compression: %s", ("False" if app_config.DEBUG else "True"))
logging.info("Database Connection String: %s", config_reader.config_data.get("Main", "mongodb-connection-string"))
logging.info(
    "Azure Blob Storage Connection String: %s",
    config_reader.config_data.get("Main", "azure-storage-account-connection-str"),
)
logging.info("Flask Asset Root: %s", app_config.ASSETS_ROOT)

# we dont need this as we run is with "flask run".
# If we run it as "python -m run" then we need this to keep the server running.
# if __name__ == "__main__":
#     app.run()


import threading
from datetime import datetime
import time
from apps.blob_management.validate_and_move_files import check_and_process_blob


def run_scheduled_job():
    while True:
        now = datetime.now().time()
        start_time = datetime.strptime("08:00:00", "%H:%M:%S")
        end_time = datetime.strptime("23:00:00", "%H:%M:%S")

        if start_time.time() <= now <= end_time.time():
            print("Running schedule task...")
            check_and_process_blob()
        else:
            print(f"Scheduled job only runs between {start_time.time()} and {end_time.time()}")

        time.sleep(5)


# Create a thread to run the scheduler
scheduler_thread = threading.Thread(target=run_scheduled_job)
scheduler_thread.daemon = True  # Set as a daemon thread so it exits when the main program exits
# Start the scheduler thread
scheduler_thread.start()
