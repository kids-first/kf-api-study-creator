import uuid
from django.db import models


class StorageBackend(models.Model):
    """
    Stores info about how to access a location in S3
    """

    class Meta:
        permissions = [
            ("list_all_storagebackend", "Show all storage_backends"),
            (
                "list_all_my_org_storagebackend",
                "Show all storage_backends owned by the user's organizations",
            ),
            (
                "view_my_org_storagebackend",
                "View storage_backends owned by the user's organizations",
            ),
            (
                "add_my_org_storagebackend",
                "Create storage_backends within the user's organizations",
            ),
        ]

    uuid = models.UUIDField(
        default=uuid.uuid4, help_text="UUID used internally"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Time when the storage_backend was created",
    )
    name = models.CharField(
        max_length=512, help_text="Name of the storage backend"
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="storage_backends",
    )
    bucket = models.CharField(
        max_length=1024, help_text="Name of the bucket in AWS"
    )
    prefix = models.CharField(
        max_length=1024, help_text="Prefix to restrict access to in the bucket"
    )
    access_key = models.CharField(
        max_length=1024, help_text="AWS access key", null=True
    )
    secret_key = models.CharField(
        max_length=1024, help_text="AWS secret key", null=True
    )
