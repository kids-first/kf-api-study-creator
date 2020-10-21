import os
import pytz
import uuid
from datetime import datetime
import django_rq
from django.conf import settings
from django.db import models


class Job(models.Model):
    """
    Logs the current state of any scheduled, recurrent jobs.
    """

    class Meta:
        permissions = [
            ("list_all_job", "Can list all jobs"),
            ("view_settings", "Can view settings"),
            ("view_queue", "Can view queues"),
        ]

    name = models.CharField(
        primary_key=True,
        max_length=400,
        null=False,
        help_text="The name of the scheduled job",
    )
    scheduler = models.CharField(
        max_length=400,
        null=False,
        default="default",
        help_text="The scheduler the Job will run on",
    )
    description = models.TextField(
        null=True, help_text="Description of the Job's role"
    )
    active = models.BooleanField(
        default=True, help_text="If the Job is active"
    )
    failing = models.BooleanField(
        default=False, help_text="If the Job is failing"
    )
    scheduled = models.BooleanField(
        default=False, help_text="If the Job is a recurring scheduled task"
    )
    created_on = models.DateTimeField(
        auto_now_add=True, null=False, help_text="Time the Job was created"
    )
    last_run = models.DateTimeField(null=True, help_text="Time of last run")
    last_error = models.TextField(
        null=True, help_text="Error message from last failure"
    )

    @property
    def enqueued_at(self):
        """
        Returns the next scheduled run time for the job or None if it is
        not a repeating job.
        """
        if not self.scheduled:
            return None

        try:
            scheduler = django_rq.get_scheduler(self.scheduler)
        except KeyError:
            # The scheduler may no longer exist,
            # so assume this is not a scheduled job
            return None
        ts = scheduler.connection.zscore(
            "rq:scheduler:scheduled_jobs", self.name
        )
        dt = datetime.fromtimestamp(ts)
        return dt.replace(tzinfo=pytz.UTC)


def _get_upload_directory(instance, filename):
    """
    Resolves the directory where a file should be stored
    """
    if settings.DEFAULT_FILE_STORAGE == "django_s3_storage.storage.S3Storage":
        prefix = f"{settings.LOG_DIR}/{filename}"
        return prefix
    else:
        return os.path.join(settings.BASE_DIR, settings.LOG_DIR, filename)


class JobLog(models.Model):
    """
    Tracks log output for a given Job run
    """

    class Meta:
        permissions = [("list_all_joblog", "Can list all job logs")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        Job,
        related_name="logs",
        help_text="The Job that this log originated from",
        on_delete=models.CASCADE,
    )

    error = models.BooleanField(
        default=False, help_text="If there was an error running the Job"
    )

    log_file = models.FileField(
        upload_to=_get_upload_directory,
        max_length=1024,
        help_text="The location where the log file is stored",
    )

    created_at = models.DateTimeField(
        auto_now_add=True, null=False, help_text="Time the log was created"
    )

    @property
    def path(self):
        """
        Returns absolute path to log download endpoint
        """
        download_url = f"/logs/{self.id}"
        return download_url
