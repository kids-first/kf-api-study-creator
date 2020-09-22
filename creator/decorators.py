import logging
import pytz
from io import StringIO
from datetime import datetime
from functools import wraps
from rq.utils import make_colorizer

from django.core.files.base import ContentFile

from creator.models import Job
from creator.jobs.models import JobLog
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
    """

    def __init__(self, job=None):
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

            self.log_preamble()

            self.logger.info(blue("Dropping into the Job process"))
            self.logger.info("")

            try:
                f(*args, **kwargs)
            except Exception as err:
                self.logger.error("")
                logger.error(
                    red(f"There was a problem running the job: {err}")
                )
                self.logger.error("")
                self._job.failing = True
                self._job.last_error = str(err)
            else:
                self.logger.info("")
                self.logger.info(green("Job exited successfully"))
                self.logger.info("")
                self._job.failing = False
                self._job.last_error = ""

            self.logger.info("Updating job status")
            self._job.last_run = datetime.utcnow()
            self._job.last_run = self._job.last_run.replace(tzinfo=pytz.UTC)
            self._job.save()

            self.close()

        return task_wrapper

    def close(self):
        logger.info("Job complete. Saving log file")

        log = JobLog(job=self._job, error=self._job.failing)

        self.logger.info(f"Saving as Job Log {yellow(str(log.id))}")

        duration = (datetime.utcnow() - self.start_time).total_seconds()
        self.logger.info(grey(f"Finished in {duration:.2f}s"))

        self.logger.info(f"Uploading log contents, goodbye! 👋")

        log.log_file.save(
            f"{int(datetime.utcnow().timestamp())}_{self._job.name}.log",
            ContentFile(self.stream.getvalue()),
        )

    def log_preamble(self):
        """
        Post some info about the codebase to the start of the log.
        """
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
