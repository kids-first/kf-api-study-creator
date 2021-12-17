from enum import Enum
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django_fsm import FSMField, transition
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator
from django.contrib.postgres.fields import JSONField

from creator.studies.models import Study
from creator.jobs.models import JobLog

User = get_user_model()


class AuditState:
    NOT_SUBMITTED = "not_submitted"
    SUBMITTING = "submitting"
    FAILED = "failed"
    SUBMITTED = "submitted"


FAIL_SOURCES = [
    AuditState.NOT_SUBMITTED,
    AuditState.SUBMITTING,
]


FILE_UPLOAD_MANIFEST_SCHEMA = {
    "required": [
        "file_location",
        "hash",
        "hash_algorithm",
        "size",
    ],
    "optional": [
    ]
}
UNIQUE_CONSTRAINT = ["file_location", "study_id"]


class ExpectedFile(models.Model):
    """
    A row in a File Upload Manifest which represents a file that was
    uploaded directly to a study's cloud storage.

    Each file record is submitted to Dewrangle, which is the system
    that will audit/determine whether the file exists in the study's cloud
    storage
    """

    class Meta:
        permissions = [
            ("list_all_expectedfiles", "Show all expected_files"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=UNIQUE_CONSTRAINT, name="unique_expected_file"
            )
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(
        default=timezone.now,
        null=True,
        help_text="When the expected file was created",
    )
    file_location = models.CharField(
        max_length=200,
        help_text="The original file location or name of the uploaded file",
    )
    hash = models.CharField(
        max_length=1024,
        help_text="The hash digest of file before upload",
    )
    hash_algorithm = models.CharField(
        max_length=500,
        help_text="The name of the hash algorithm used to compute"
        " the file hash",
    )
    size = models.BigIntegerField(
        validators=[
            MinValueValidator(0, "File size must be a positive number")
        ],
        help_text="Size of the uploaded file in bytes",
    )
    custom_fields = JSONField(
        default=dict,
        help_text="Additional fields in the file upload manifest that need"
        " to be captured",
    )
    audit_state = FSMField(
        default=AuditState.NOT_SUBMITTED,
        help_text="The state of the expected file in the submission process to"
        "Dewrangle",
    )
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE,
        related_name="expected_files",
        help_text="id of the study whose cloud storage this file was uploaded"
        " to",
    )

    @transition(
        field=audit_state,
        source=[AuditState.NOT_SUBMITTED, AuditState.FAILED],
        target=AuditState.SUBMITTING
    )
    def start_submission(self):
        """
        Begin the process to submit this expected file to the auditing
        system.
        """
        pass

    @transition(field=audit_state, source=AuditState.SUBMITTING,
                target=AuditState.SUBMITTED)
    def complete_submission(self):
        """
        Mark completion of the expected file being submitted to the
        auditing system
        """
        pass

    @transition(
        field=audit_state, source=FAIL_SOURCES, target=AuditState.FAILED
    )
    def fail_submission(self):
        """
        Fail submission of the expected file to the audit system due
        to some unexpected error
        """
        pass
