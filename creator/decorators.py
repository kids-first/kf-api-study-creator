import sys
import logging
import pytz
import traceback
from io import StringIO
from datetime import datetime
from functools import wraps
from rq.utils import make_colorizer

from django.conf import settings
from django.core.files.base import ContentFile
from django_s3_storage.storage import S3Storage

from creator.releases.models import Release, ReleaseTask
from creator.jobs.models import Job, JobLog
from creator.version_info import VERSION, COMMIT

logger = logging.getLogger(__name__)

green = make_colorizer("green")
yellow = make_colorizer("yellow")
blue = make_colorizer("blue")
grey = make_colorizer("lightgray")
red = make_colorizer("red")


class task:
    """
    A decorator to uniformly setup tasks that get enqueued for workers to
    execute.

    If the wrapped task contains a release_id or task_id, save the log to the
    appropriate model so that it may be retrieved relationally.
    """

    def __init__(self, job=None):
        self._release = None
        self._task = None
        self.job = job
        self.logger = logging.getLogger("TaskLogger")
        self.start_time = datetime.utcnow()

        self.stream = StringIO()
        handler = logging.StreamHandler(self.stream)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        # Add the handler to the base module to capture all log output
        logging.getLogger("creator").addHandler(handler)

    def __call__(self, f):
        @wraps(f)
        def task_wrapper(*args, **kwargs):
            try:
                self._job = Job.objects.get(name=self.job)
            except Job.DoesNotExist:
                logger.info(
                    f"The {self.job} job does not exist. "
                    "Registering a new unsceduled-job for it."
                )
                self._job = Job(name=self.job, active=True, scheduled=False)

            if not self._job.active:
                logger.info(
                    f"The {self._job.name} job is not active, will not run"
                )
                return

            # If the function recieves a release id, store it so we can link
            # the log back to it later
            if "release_id" in kwargs:
                self._release = Release.objects.get(
                    pk=kwargs.get("release_id")
                )
            # Do the same if the function recieves a task id
            if "task_id" in kwargs:
                self._task = ReleaseTask.objects.get(pk=kwargs.get("task_id"))

            self.log_preamble()

            self.logger.info(blue("Dropping into the Job process"))
            self.logger.info("")

            # Used to store any exception that gets raised during execution
            exception = None

            try:
                f(*args, **kwargs)
            except Exception as err:
                exception = err
                logger.error(
                    red(
                        f"There was a problem running the job:\n"
                        f"{traceback.format_exc()}"
                    )
                )
                self._job.failing = True
                self._job.last_error = str(err)
            else:
                self.logger.info("")
                self.logger.info(green("Job exited successfully"))
                self.logger.info("")
                self._job.failing = False
                self._job.last_error = ""

            self._job.last_run = datetime.utcnow()
            self._job.last_run = self._job.last_run.replace(tzinfo=pytz.UTC)
            self._job.save()

            self.close()

            # If there was some exception, throw it now after the Job status
            # has been updated
            if exception:
                raise exception

        return task_wrapper

    def close(self):
        """
        Close out the log stream for the task by appending it with a couple
        final details.
        A new log will be created or an existing log will be appended if the
        there is already a log existing for the Job invocation.
        """
        duration = (datetime.utcnow() - self.start_time).total_seconds()

        # Try to get an existing log if one exists for this job or else create
        # a new one
        log = self._get_existing_job_log()
        existing_log_contents = ""

        if log is None:
            log = JobLog(job=self._job, error=self._job.failing)

        # Need to manually configure the log's bucket if we're using S3 storage
        if (
            settings.DEFAULT_FILE_STORAGE
            == "django_s3_storage.storage.S3Storage"
        ):
            log.log_file.storage = S3Storage(
                aws_s3_bucket_name=settings.LOG_BUCKET
            )

        if log is not None:
            # This may be a new log with no log file saved yet so don't panic
            # if there is no contents to read
            try:
                existing_log_contents = log.log_file.open().read().decode()
            except ValueError:
                pass

        self.logger.info(
            f"Job complete after {duration:.2f}s. "
            f"Saving as Job Log {yellow(str(log.id))}, "
            f"goodbye! 👋"
        )

        name = (
            f"{datetime.utcnow().strftime('%Y/%m/%d/')}"
            f"{int(datetime.utcnow().timestamp())}_{self._job.name}.log"
        )

        content = existing_log_contents + self.stream.getvalue()
        log.log_file.save(name, ContentFile(content))
        log.save()

        # Save the log to the release and/or task, if there is one
        if self._release:
            self._release.job_log = log
            self._release.save(update_fields=["job_log"])
        if self._task:
            self._task.job_log = log
            self._task.save(update_fields=["job_log"])

    def _get_existing_job_log(self):
        """
        If this task executed for a job that has an ongoing log, such as for
        releases or release tasks, try to resolve that job log and return it.
        Otherwise, return None if we cannot resolve an existing job log.
        """

        if self._release and self._release.job_log is not None:
            return self._release.job_log

        if self._task and self._task.job_log is not None:
            return self._task.job_log

        return None

    def log_preamble(self):
        """
        Post some info about the codebase to the start of the log.
        If the job invocation already has a log, don't log the header as it's
        already been included in an earlier log.
        """
        log = self._get_existing_job_log()
        if log:
            self.logger.info("")
            self.logger.info(
                blue(f"Re-attaching to Job Log ") + yellow(str(log.id))
            )
            self.logger.info("")
            return

        self.logger.info(blue(f"╔{'═'*48}╗"))
        self.logger.info(blue(f"║ {'Study Creator API Worker':<46} ║"))
        self.logger.info(blue(f"╠{'═'*48}╣"))
        self.logger.info(blue(f"║ Version: {VERSION:<37} ║"))
        self.logger.info(blue(f"║ Job: {self.job:<41} ║"))
        self.logger.info(
            blue(f"║ Date: {datetime.utcnow().isoformat():<40} ║")
        )
        self.logger.info(blue(f"╚{'═'*48}╝"))
        self.logger.info("")
