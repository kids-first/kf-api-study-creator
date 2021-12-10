import uuid
from django.db import models


class Organization(models.Model):
    """
    The top-most level of categorization of data. Models an institution that
    may contain multiple studies and users.
    """

    class Meta:
        permissions = [
            ("list_all_organization", "Can list all organizations"),
            (
                "view_my_organization",
                "Can list organizations that the user belongs to",
            ),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dewrangle_id = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        help_text="Unique identifier of the org in Dewrangle"
    )
    name = models.CharField(
        max_length=1024, null=False, help_text="The name of the organization"
    )
    description = models.TextField(
        null=True, blank=True, help_text="Description of the organization"
    )
    email = models.EmailField(
        null=True, blank=True, help_text="Email address for the organization"
    )
    website = models.URLField(
        null=True, blank=True, help_text="Url for the organization's website"
    )
    image = models.URLField(
        null=True,
        blank=True,
        help_text="Url for the organization's display image",
    )
    created_on = models.DateTimeField(
        auto_now_add=True,
        null=False,
        help_text="Time the organization was created",
    )
    members = models.ManyToManyField(
        "creator.User",
        related_name="organizations",
        help_text="Users that belong to this organization",
    )
