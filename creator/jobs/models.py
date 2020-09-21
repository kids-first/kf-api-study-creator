import os
import pytz
import uuid
from django.conf import settings
from django.db import models

from creator.models import Job


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
