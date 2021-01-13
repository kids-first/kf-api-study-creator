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

    related_models may be specified to attach the generated job_log to other
    models.
    This takes one of two forms:
        {Model1: "kwarg_name_for_pk", Model2: ...}
            or
        {Model1: ModelInstance, Model2: ...}
    Any number of relations may be specified in this way.
    Note that an object's model must have a 'job_log' foreign key to the JobLog
    table in order to be saved.
    If there is no foreign key, or no object instance can be resolved, it will
    be skipped and no relation saved.
    When calling the job function, it is important that the appropriate keyword
    argument is passed, positional arguments will not be able to be resolved.
    """

    def __init__(self, job=None, related_models=None):
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

        self.related_models = related_models or {}
        self.related_instances = []

    def _resolve_related(self, *args, **kwargs):
        """
        Attempt to resolve arguments to the task to a model instance in the
        database so we can link them back at save.
        """
        for model, inst in self.related_models.items():
            if inst not in kwargs:
                logger.warning(
                    f"Could not find '{inst}' in the keyword arguments. "
                    f"Will not be able to attach logs to a related {model}"
                )
                continue

            # If the argument is an actual object of the model, use that.
            # Otherwise, try to use the argument to look up an object by pk
            if isinstance(kwargs[inst], model):
                instance = kwargs[inst]
            else:
                try:
                    instance = model.objects.get(pk=kwargs[inst])
                except model.DoesNotExist:
                    continue

            if not hasattr(instance, "job_log"):
                logger.warning(
                    f"Cannot attach log to {instance}. "
                    "Models must have a 'job_log' foreign key relation"
                )
                continue

            self.related_instances.append(instance)

    def _attach_related(self, log):
        """
        Attaches a given log to any related instances that are stored
        """
        for instance in self.related_instances:
            # Only update if the job_log has not yet been saved, otherwise will
            # throw a 'did not affect any rows' error.
            if instance.job_log is None:
                instance.job_log = log
                instance.save(update_fields=["job_log"])

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

            self._resolve_related(*args, **kwargs)

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

        # Retrieve any existing job logs from related models so we can append
        # this session's log output to them. If there are no existing logs,
        # we will create a new one
        job_logs = self._get_existing_job_logs()
        if len(job_logs) == 0:
            job_logs = [JobLog(job=self._job, error=self._job.failing)]

        self.logger.info(
            f"Job complete after {duration:.2f}s. "
            f"Saving to Job Logs: "
            f"{', '.join(yellow(str(log.id)) for log in job_logs)}, "
            f"goodbye! 👋"
        )

        for job_log in job_logs:
            self._append_previous_log(job_log)
            self._attach_related(job_log)

    def _append_previous_log(self, job_log):
        """
        Append a given job_log's file with the log stream from this session
        """
        # Need to manually configure the log's bucket if we're using S3 storage
        if (
            settings.DEFAULT_FILE_STORAGE
            == "django_s3_storage.storage.S3Storage"
        ):
            job_log.log_file.storage = S3Storage(
                aws_s3_bucket_name=settings.LOG_BUCKET
            )

        existing_log_contents = ""
        # This may be a new log with no log file saved yet so don't panic
        # if there is no contents to read
        try:
            existing_log_contents = job_log.log_file.open().read().decode()
            name = job_log.log_file.name
            # The logging directory is included in the name already and will
            # be prepended when we write back to the storage, so remove it now
            name = name.replace(f"{settings.LOG_DIR}", "")
        except ValueError:
            name = (
                f"{datetime.utcnow().strftime('%Y/%m/%d/')}"
                f"{int(datetime.utcnow().timestamp())}_{self._job.name}.log"
            )
        except FileNotFoundError as err:
            self.logger.error(f"Could not read log file: {err}")
            return

        content = existing_log_contents + self.stream.getvalue()
        job_log.log_file.save(name, ContentFile(content))
        job_log.save()

    def _get_existing_job_logs(self):
        """
        Resolve the unique set of related instances' job_logs
        """
        return {
            instance.job_log
            for instance in self.related_instances
            if instance.job_log is not None
        }

    def log_preamble(self):
        """
        Post some info about the codebase to the start of the log.
        If the job invocation already has a log, don't log the header as it's
        already been included in an earlier log.
        """
        job_logs = self._get_existing_job_logs()
        if len(job_logs) > 0:
            self.logger.info("")
            self.logger.info(
                blue(f"Re-attaching to Job Log ")
                + ", ".join([yellow(str(log.id)) for log in job_logs])
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
