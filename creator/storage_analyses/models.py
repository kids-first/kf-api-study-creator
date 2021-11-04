from enum import Enum
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django_fsm import FSMField, transition
from django.utils import timezone
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.validators import MinValueValidator

from creator.fields import kf_id_generator
from creator.studies.models import Study
from creator.files.models import Version
from creator.jobs.models import JobLog

User = get_user_model()


class ResultEnum(Enum):
    matched = "matched"
    missing = "missing"
    differ = "differ"
    inventory_only = "inventory_only"
    unknown = "unknown"


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
    @property
    def file_audit_table_path(self):
        """
        Returns absolute path to the download endpoint for the file audit table
        """
        download_url = (
            f"/download/study/{study.pk}/storage-analysis/file-audit-table"
        )
        return download_url


class FileAudit(models.Model):
    """
    A row in the file audit table of the storage analysis dashboard

    The file audit table is the result of joining all file upload manifests
    with an S3 inventory in an effort to compare a file in the upload manifests
    vs what was actually found in cloud storage.
    """

    class Meta:
        permissions = [
            ("list_all_fileaudits", "Show all file_audits"),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(
        default=timezone.now,
        null=True,
        help_text="When the file audit was created",
    )
    result = models.CharField(
        max_length=50,
        choices=[(r.name, r.value) for r in ResultEnum],
        help_text="Result of the file audit",
    )
    source_filename = models.CharField(
        max_length=256,
        help_text="The original name of the uploaded file",
        null=True,
        blank=True
    )
    expected_url = models.URLField(
        null=True, blank=True, help_text="Url of the file in cloud storage"
    )
    expected_hash = models.CharField(
        max_length=256,
        help_text="The hash digest of file before upload",
        null=True,
        blank=True
    )
    actual_hash = models.CharField(
        max_length=256,
        help_text="The hash digest of file in cloud storage",
        null=True,
        blank=True
    )
    expected_size = models.BigIntegerField(
        validators=[
            MinValueValidator(0, "File size must be a positive number")
        ],
        help_text="Expected size of the uploaded file in bytes",
        null=True,
        blank=True,
    )
    actual_size = models.BigIntegerField(
        validators=[
            MinValueValidator(0, "File size must be a positive number")
        ],
        help_text="Actual size of the file on cloud storage in bytes",
        null=True,
        blank=True,
    )
    hash_algorithm = models.CharField(
        max_length=256,
        help_text="The name of the hash algorithm used to compute"
        " the file hash",
        null=True,
        blank=True
    )
    custom_fields = JSONField(
        default=dict,
        help_text="Any other columns in the file upload manifest that "
        "should be included in the file audit table",
    )
    storage_analysis = models.ForeignKey(
        StorageAnalysis,
        on_delete=models.CASCADE,
        null=True,
        related_name="file_audits",
        help_text="id of the storage analysis this audit belongs to",
    )
