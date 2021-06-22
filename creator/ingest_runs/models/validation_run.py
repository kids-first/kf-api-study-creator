import os
import uuid

import django_rq
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from creator.ingest_runs.common.model import IngestProcess
from creator.data_reviews.models import DataReview
from creator.files.models import Version


User = get_user_model()


def _get_upload_directory(validation_resultset, filename):
    """
    Resolves the directory where a file should be stored
    """
    if settings.DEFAULT_FILE_STORAGE == "django_s3_storage.storage.S3Storage":
        prefix = f"{settings.UPLOAD_DIR}/{filename}"
        return prefix
    else:
        # Validation_resultset should always have a study from its
        # associated data_review
        bucket = validation_resultset.study.bucket
        directory = f"{settings.UPLOAD_DIR}/{bucket}/"
        return os.path.join(directory, filename)


class ValidationRun(IngestProcess):
    """
    Request to validate file versions in a data review
    """

    class Meta(IngestProcess.Meta):
        permissions = [
            ("list_all_validationrun", "Show all validation_runs"),
            ("cancel_validationrun", "Cancel an validation_run"),
            (
                "add_my_study_validationrun",
                "Can start validation runs for studies user is a member of",
            ),
            (
                "cancel_my_study_validationrun",
                "Can cancel validation runs for studies user is a member of",
            ),
            (
                "view_my_study_validationrun",
                "Can view validation runs for studies user is a member of",
            ),
        ]

    success = models.BooleanField(
        null=True,
        blank=True,
        default=False,
        help_text="Whether the validation run resulted in all tests passing",
    )
    progress = models.IntegerField(
        null=True,
        blank=True,
        default=0,
        help_text="The the percentage of the validation run that has been "
        "completed",
    )
    data_review = models.ForeignKey(
        DataReview,
        on_delete=models.CASCADE,
        null=True,
        related_name="validation_runs",
    )

    @property
    def versions(self):
        """
        Get file versions from the associated DataReview
        """
        if self.data_review:
            return self.data_review.versions
        else:
            return Version.objects.none()

    @property
    def study(self):
        """
        Get Study from the associated data review
        """
        if self.data_review:
            return self.data_review.study

    def clean(self):
        """
        Validate (no pun intended) a ValidationResult instance
        """
        if self.study is None:
            raise ValidationError(
                "A ValidationRun must have an associated DataReview "
                "with a non-null study"
            )


class ValidationResultset(models.Model):
    """
    Validation results from a completed validation run
    """

    report_filename = "validation_results.md"
    results_filename = "validation_results.json"

    class Meta:
        permissions = [
            ("list_all_validationresultset", "Show all validation_resultsets"),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Time when the validation result set was created",
    )
    data_review = models.OneToOneField(
        DataReview,
        null=True,
        blank=True,
        related_name="validation_resultset",
        on_delete=models.CASCADE,
        help_text=(
            "The associated data review this validation result set belongs to"
        ),
    )
    report_file = models.FileField(
        upload_to=_get_upload_directory,
        null=True,
        blank=True,
        max_length=512,
        help_text=(
            "Field to track the storage location of the user friendly "
            "validation report"
        ),
    )
    results_file = models.FileField(
        upload_to=_get_upload_directory,
        null=True,
        blank=True,
        max_length=512,
        help_text=(
            "Field to track the storage location of the raw validation "
            "results"
        ),
    )
    passed = models.IntegerField(
        null=True,
        blank=True,
        default=0,
        help_text="The number of validation tests that passed",
    )
    failed = models.IntegerField(
        null=True,
        blank=True,
        default=0,
        help_text="The number of validation tests that failed",
    )
    did_not_run = models.IntegerField(
        null=True,
        blank=True,
        default=0,
        help_text="The number of validation tests that did not run",
    )

    @property
    def study(self):
        """
        Get Study from the file versions in the associated data review
        """
        if self.data_review:
            return self.data_review.study

    @property
    def report_path(self):
        """
        Returns absolute path to the validation report file download endpoint
        """
        review_id = self.data_review.kf_id
        download_url = f"/download/data_review/{review_id}/validation/report"
        return download_url

    @property
    def results_path(self):
        """
        Returns absolute path to the validation results file download endpoint
        """
        review_id = self.data_review.kf_id
        download_url = f"/download/data_review/{review_id}/validation/results"
        return download_url

    def clean(self):
        """
        Validate (no pun intended) a ValidationResultset instance
        """
        if self.study is None:
            raise ValidationError(
                "A ValidationResultset must have an associated DataReview "
                "with a non-null study"
            )
