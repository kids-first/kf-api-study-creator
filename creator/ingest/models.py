import uuid
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth import get_user_model
from django.utils import timezone

from creator.files.models import Version

User = get_user_model()


class Validation(models.Model):
    """
    Tracks validation results.
    """

    class Meta:
        permissions = [
            ("list_all_validation", "Can list all validations"),
            (
                "view_my_study_validation",
                "Can view all validations in studies user is a member of",
            ),
            (
                "add_my_study_validation",
                "Can create validations for documents in studies the user "
                "is a member of",
            ),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    versions = models.ManyToManyField(
        Version,
        related_name="validations",
        help_text="Versions used as input to the validation",
    )

    result = JSONField(default=dict)

    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="validations",
        help_text="The user who created this validation",
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        null=False,
        help_text="Time the validiation was created",
    )
