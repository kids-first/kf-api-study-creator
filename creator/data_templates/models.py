import uuid
from django.db import models
from django.contrib.auth import get_user_model

from creator.fields import kf_id_generator
from creator.organizations.models import Organization

User = get_user_model()


def template_id():
    return kf_id_generator("DT")


class DataTemplate(models.Model):
    """
    A data submission template with versions

    The Template model represents the essence of the data template just like
    File does with Version, and it provides a container for the versions
    of the template
    """

    class Meta:
        permissions = [
            ("list_all_datatemplate", "Show all data_template"),
        ]

    id = models.CharField(
        max_length=11,
        primary_key=True,
        default=template_id,
        help_text="Human friendly ID assigned to the data template",
    )
    uuid = models.UUIDField(
        default=uuid.uuid4, help_text="UUID used internally"
    )
    created_at = models.DateTimeField(
        auto_now=True,
        null=True,
        help_text="Time when the data template was created",
    )
    modified_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Time when the data template was modified",
    )
    organization = models.ForeignKey(
        Organization,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="data_templates",
        help_text="The user who created the data template",
    )
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="data_templates",
        help_text="The user who created the data template",
    )
    name = models.CharField(
        max_length=256, help_text="Name of the data template"
    )
    description = models.TextField(
        max_length=10000,
        null=True,
        blank=True,
        help_text="Description of data template",
    )
    icon = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        help_text="Name of the Font Awesome icon to use when displaying the "
        "template"
    )
