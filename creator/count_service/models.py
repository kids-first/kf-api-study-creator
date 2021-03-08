import uuid
import requests
import json
import logging
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django_fsm import FSMField, transition
from semantic_version import Version
from semantic_version.django_fields import VersionField

from creator.authentication import service_headers
from creator.fields import kf_id_generator
from creator.studies.models import Study
from creator.releases.models import Release
from creator.jobs.models import JobLog

logger = logging.getLogger(__name__)

User = get_user_model()


class CountTask(models.Model):
    """
    Tracks state of the Count Release Service which generates Study summaries
    for releases.
    """

    kf_id = models.CharField(max_length=11, primary_key=True, null=False)
    state = FSMField(
        default="pending", help_text="The current state of the task"
    )
    progress = models.IntegerField(
        default=0,
        help_text="Optional field"
        " representing what percentage of the task"
        " has been completed",
    )
    job_log = models.ForeignKey(
        JobLog,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="count_service_tasks",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Time the task was created"
    )
    release = models.ForeignKey(
        Release,
        on_delete=models.CASCADE,
        related_name="count_tasks",
        help_text="The release that this task is running for",
    )

    @transition(field=state, source="pending", target="running")
    def start(self):
        pass

    @transition(field=state, source="running", target="staged")
    def stage(self):
        pass

    @transition(field=state, source="staged", target="publishing")
    def publish(self):
        pass

    @transition(field=state, source="publishing", target="complete")
    def complete(self):
        pass

    @transition(field=state, source="*", target="failed")
    def failed(self):
        return

    @transition(field=state, source="*", target="canceled")
    def cancel(self):
        pass


class StudySummary(models.Model):
    """
    A summary of a study's entity counts.
    """

    class Meta:
        permissions = [
            ("list_all_studysummary", "Can list all study summaries"),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Time the summary was created"
    )
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE,
        related_name="summaries",
        help_text="Study that this summary was generated for",
    )
    count_task = models.ForeignKey(
        CountTask,
        on_delete=models.SET_NULL,
        null=True,
        related_name="summaries",
        help_text="Count Task that created this summary",
    )
    counts = JSONField(default=dict, help_text="Entity counts for the study")
