import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django_fsm import FSMField, transition
from django.utils import timezone
from django.conf import settings
from django.contrib.postgres.fields import JSONField

from creator.fields import kf_id_generator
from creator.studies.models import Study
from creator.files.models import Version
from creator.jobs.models import JobLog

User = get_user_model()


def storage_analysis_id():
    return kf_id_generator("SA")


def _get_upload_directory(storage_analysis, filename):
    """
    Resolves the directory where a file should be stored
    """
    if settings.DEFAULT_FILE_STORAGE == "django_s3_storage.storage.S3Storage":
        prefix = f"{settings.UPLOAD_DIR}/{filename}"
        return prefix
    else:
        bucket = storage_analysis.study.bucket
        directory = f"{settings.UPLOAD_DIR}/{bucket}/"
        return os.path.join(directory, filename)


class StorageAnalysis(models.Model):
    """
    An analysis of files in study's a cloud storage
    """

    class Meta:
        permissions = [
            ("list_all_storageanalysis", "Show all storage_analyses"),
        ]

    id = models.CharField(
        max_length=11,
        primary_key=True,
        default=storage_analysis_id,
        help_text="Human friendly ID assigned to the storage_analysis",
    )
    uuid = models.UUIDField(
        default=uuid.uuid4, help_text="UUID used internally"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        null=True,
        help_text="When the storage_analysis was created",
    )
    refreshed_at = models.DateTimeField(
        null=True,
        help_text="When the stored analysis was recomputed",
    )
    stats = JSONField(
        default=dict,
        help_text="The the numerical storage analysis stats",
    )
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE,
        null=True,
        related_name="storage_analyses",
    )
    file_audit_table = models.FileField(
        upload_to=_get_upload_directory,
        null=True,
        blank=True,
        max_length=512,
        help_text=(
            "Field to track the storage location file audit table"
        ),
    )
    @property
    def file_audit_table_path(self):
        """
        Returns absolute path to the download endpoint for the file audit table
        """
        download_url = (
            f"/download/study/{study.pk}/storage-analysis/file-audit-table"
        )
        return download_url
