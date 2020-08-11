from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth import get_user_model
from django.utils import timezone

from creator.files.models import Version

User = get_user_model()


class Analysis(models.Model):
    """
    An analysis run on a file.
    """

    class Meta:
        permissions = [
            ("list_all_analysis", "Can list all analyses"),
            (
                "view_my_analysis",
                "Can view all analyses in studies user is a member of",
            ),
            (
                "add_my_study_analysis",
                "Can add analyses to studies the user is a member of",
            ),
            (
                "change_my_study_analysis",
                "Can change analyses in studies the user is a member of",
            ),
        ]

    known_format = models.BooleanField(
        help_text="If this file is of a recognized format"
    )
    error_message = models.TextField(
        null=True,
        help_text=(
            "Error message resulting from a failed attempt to analyze "
            "a version"
        ),
    )

    columns = JSONField(default=dict)

    nrows = models.PositiveIntegerField(
        default=0, help_text="The number of rows in the file"
    )
    ncols = models.PositiveIntegerField(
        default=0, help_text="The number of columns in the file"
    )

    version = models.OneToOneField(
        Version,
        related_name="analysis",
        help_text=("The file that this analsis belongs to"),
        on_delete=models.CASCADE,
    )

    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="analyses",
        help_text="The user who created this analysis",
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        null=False,
        help_text="Time the version was created",
    )
