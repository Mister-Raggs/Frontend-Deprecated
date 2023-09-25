from importlib import import_module
import os, logging
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler

from apps.common import config_reader
from apps.jobs import app_jobs_scheduler


def collect_and_schedule_jobs() -> BackgroundScheduler:
    app_base_dir = config_reader.config_data.get("Main", "app_base_dir")
    scheduled_jobs_folder = Path(app_base_dir + "/apps/jobs").absolute()

    for job_file in os.scandir(scheduled_jobs_folder):
        if (
            not job_file.is_dir()
            and not job_file.name.startswith("__")
            and not job_file.name.startswith("job_scheduler_factory")
        ):
            module_name = job_file.name.replace(".py", "")
            module_path = f"apps.jobs.{module_name}"
            module = import_module(f"{module_path}")
            if (
                hasattr(module, "job_task")
                and hasattr(module, "JOB_NAME")
                and hasattr(module, "SCHEDULE_INTERVAL_IN_SECONDS")
            ):
                # add the job to scheduler
                app_jobs_scheduler.add_job(
                    module.job_task,
                    trigger="interval",
                    name=module.JOB_NAME,
                    seconds=module.SCHEDULE_INTERVAL_IN_SECONDS,
                    misfire_grace_time=600,
                )
            else:
                logging.warning(
                    "Skipping Job module %s as it does not seem to have a function named as 'job_task'.",
                    module.__name__,
                )

    # log jobs list
    jobs_list = app_jobs_scheduler.get_jobs()
    for job in jobs_list:
        logging.info(
            "Registered Job (id: %s, name: %s, trigger: %s)",
            job.id,
            job.name,
            job.trigger,
        )

    # start scheduler
    app_jobs_scheduler.start()

    return app_jobs_scheduler
