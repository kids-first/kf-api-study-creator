import uuid
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.contrib.auth import get_user_model

from creator.fields import kf_id_generator
from creator.studies.models import Study
from creator.organizations.models import Organization

User = get_user_model()


def template_id():
    return kf_id_generator("DT")


def template_version_id():
    return kf_id_generator("TV")


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
        auto_now_add=True,
        null=True,
        help_text="Time when the data template was created",
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        null=True,
        help_text="Time when the data template was modified",
    )
    organization = models.ForeignKey(
        Organization,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="data_templates",
        help_text="The organization that owns the data template",
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
        help_text="Description of data template",
    )
    icon = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        help_text="Name of the Font Awesome icon to use when displaying the "
        "template in the frontend web application",
    )

    @property
    def released(self):
        """
        Determines whether the data template is being used in any studies

        A data template is being used in a study if one or more of its
        versions has been assigned to a study
        """
        assigned_to_studies = (
            TemplateVersion.objects.filter(data_template__pk=self.pk)
            .exclude(studies=None)
            .count()
        )
        return assigned_to_studies > 0


class TemplateVersion(models.Model):
    """
    A version of a specific data submission template

    Encapsulates the data template's field definitions (e.g. columns,
    accepted values, instructions for populating, etc.)
    """

    class Meta:
        permissions = [
            ("list_all_templateversion", "Show all template_version"),
        ]

    id = models.CharField(
        max_length=11,
        primary_key=True,
        default=template_version_id,
        help_text="Human friendly ID assigned to the template version",
    )
    uuid = models.UUIDField(
        default=uuid.uuid4, help_text="UUID used internally"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Time when the template version was created",
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        null=True,
        help_text="Time when the template version was modified",
    )
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="template_versions",
        help_text="The user who created the template version",
    )
    description = models.TextField(
        max_length=10000,
        help_text="Description of changes in this template version",
    )
    field_definitions = JSONField(
        default=dict,
        help_text="The field definitions for this template version",
    )
    data_template = models.ForeignKey(
        DataTemplate,
        on_delete=models.CASCADE,
        related_name="template_versions",
        help_text="The data template this template version belongs to",
    )
    studies = models.ManyToManyField(
        Study,
        related_name="template_versions",
        help_text="The studies this template version is assigned to",
    )

    @property
    def organization(self):
        """
        Organization that owns this template version
        """
        return self.data_template.organization

    @property
    def released(self):
        """
        Determines whether the template version is being used in any studies
        """
        return self.studies.count() > 0

    def clean(self):
        """
        Validate this template version

        TODO Validate field definitions
        """
        pass