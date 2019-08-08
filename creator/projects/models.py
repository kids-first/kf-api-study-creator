from django.db import models
from creator.studies.models import Study


class Project(models.Model):
    """
    Represents a project created in Cavatica.
    Documentation: http://docs.cavatica.org/docs/projects
    """

    project_id = models.CharField(
        primary_key=True,
        max_length=200,
        null=False,
        help_text="The Cavatica project identifier",
    )
    name = models.CharField(
        max_length=500,
        null=False,
        help_text="The name of the Cavatica project",
    )
    description = models.TextField(
        null=False,
        help_text="The description markdown of the Cavatica project",
    )
    url = models.CharField(
        max_length=500, null=False, help_text="The url of the Cavatica project"
    )
    project_type = models.CharField(
        max_length=3,
        choices=(("HAR", "harmonization"), ("DEL", "delivery")),
        default="HAR",
        help_text="The Cavatica project type",
    )
    workflow_type = models.CharField(
        max_length=200,
        choices=WORKFLOW_TYPES,
        null=True,
        help_text="The Cavatica project workflow type",
    )
    created_by = models.CharField(
        max_length=200,
        null=False,
        help_text="The user who created the Cavatica project",
    )
    created_on = models.DateTimeField(
        auto_now_add=False,
        null=False,
        help_text="Time the Cavatica project was created",
    )
    modified_on = models.DateTimeField(
        auto_now=False, null=False, help_text="Time of last modification"
    )
    study = models.ForeignKey(
        Study,
        related_name="projects",
        help_text="The study this project belongs to",
        on_delete=models.SET_NULL,
        null=True,
    )

    def __str__(self):
        return self.project_id
