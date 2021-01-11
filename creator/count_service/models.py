import uuid
import requests
import json
import logging
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django_fsm import FSMField, transition
from semantic_version import Version
from semantic_version.django_fields import VersionField

from creator.authentication import service_headers
from creator.fields import kf_id_generator
from creator.studies.models import Study
from creator.jobs.models import JobLog

logger = logging.getLogger(__name__)

User = get_user_model()


class CountTask(models.Model):
    """"""

    kf_id = models.CharField(max_length=11, primary_key=True, null=False)
    state = FSMField(
        default="initialized", help_text="The current state of the task"
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

    @transition(field=state, source="initialized", target="running")
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
