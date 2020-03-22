from django.db import models
from django.contrib.postgres.fields import JSONField
from creator.studies.models import Study


class Bucket(models.Model):
    """
    Represents a study bucket in S3
    """

    class Meta:
        permissions = [
            ("list_all_bucket", "Can list all buckets"),
            ("link_bucket", "Can link a bucket to a study"),
            ("unlink_bucket", "Can unlink a bucket to a study"),
        ]

    name = models.CharField(
        primary_key=True,
        max_length=512,
        null=False,
        help_text="The name of the bucket in S3",
    )
    created_on = models.DateTimeField(
        null=False, help_text="Time the bucket was created"
    )
    study = models.ForeignKey(
        Study,
        related_name="buckets",
        help_text="The study this bucket belongs to",
        on_delete=models.SET_NULL,
        null=True,
    )
    deleted = models.BooleanField(
        null=False,
        default=False,
        help_text="Whether this bucket has been deleted from S3",
    )
