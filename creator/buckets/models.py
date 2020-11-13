import uuid
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


class BucketInventory(models.Model):
    """
    Represents and summarizes a bucket inventory created by S3
    """

    class Meta:
        permissions = [
            ("list_all_bucketinventory", "Show all bucket_inventories")
        ]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    bucket = models.ForeignKey(
        Bucket,
        related_name="inventories",
        help_text="The bucket this inventory belongs to",
        on_delete=models.SET_NULL,
        null=True,
    )
    creation_date = models.DateTimeField(
        null=False,
        help_text=(
            "The date the inventory was generated. "
            "Not to be confused with the created_at time which is when it was "
            "registered in the database"
        ),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=False,
        help_text="Time when the bucket inventory was created",
    )
    key = models.FileField(
        max_length=512,
        help_text="Field to track the storage location of the inventory",
    )
    manifest = JSONField(
        default=dict,
        help_text=(
            "Copy of the manifest.json for the inventory that was saved in s3"
        ),
    )
    summary = JSONField(
        default=dict, help_text="Summary analysis of the inventory"
    )
    imported = models.BooleanField(
        default=False, help_text="Whether this inventory was imported or not"
    )
