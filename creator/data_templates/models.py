import os
import uuid

import pandas
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from kf_lib_data_ingest.common.io import read_df

from creator.fields import kf_id_generator
from creator.studies.models import Study
from creator.organizations.models import Organization
from creator.data_templates.field_definitions_schema import (
    FieldDefinitionsSchema
)


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
        "template in the frontend web application"
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

    field_definitions_schema = FieldDefinitionsSchema()

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

    @property
    def template_dataframe(self):
        """
        Create the content of the tabular data submission file

        This will become the content of the template file that users will
        populate after they download the template files
        """
        return pandas.DataFrame([
            {
                f["label"]: ""
                for f in self.field_definitions["fields"]
            }
        ])

    @property
    def field_definitions_dataframe(self):
        """
        Create the content for the tabular field definitions file

        This will become the content of the field definitions file when
        the user requests to download the template files
        """
        def format_accepted(value):
            """
            Convert list to delimited str
            """
            if isinstance(value, list):
                value = ",".join(value)
            return value

        df = pandas.DataFrame(self.field_definitions["fields"])
        df = df[FieldDefinitionsSchema.key_order]
        # Don't include the field key for now
        if "key" in df.columns:
            df.drop(columns=["key"], axis=1, inplace=True)
        df["accepted_values"] = df["accepted_values"].apply(
            format_accepted
        )
        df.columns = [
            " ".join([w.title() for w in col.split("_")])
            for col in df.columns.tolist()
        ]

        return df

    def clean(self):
        """
        Validate template version
        """
        # Try to fix any human errors in the data before validating against
        # the field definitions schema (See FieldDefinitionsSchema.clean)
        self.field_definitions = (
            self.field_definitions_schema.load(self.field_definitions)
        )
