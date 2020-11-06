import hashlib
import uuid
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django_fsm import FSMField, transition

from creator.files.models import Version
from creator.jobs.models import JobLog

User = get_user_model()


class IngestRun(models.Model):
    """
    An ingest run follows the process of ingesting a set of versions into
    the Dataservice.
    """

    class Meta:
        permissions = [
            ("list_all_ingestrun", "Show all ingest runs"),
            ("cancel_ingestrun", "Cancel an ingest run"),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(
        null=False, help_text="Time when the ingest run was created"
    )

    job_log = models.ForeignKey(
        JobLog,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="job_log",
    )

    state = FSMField(
        default="waiting", help_text="The current state of the ingest run"
    )

    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="releases",
        help_text="The user who created the release",
    )

    versions = models.ManyToManyField(
        Version,
        related_name="ingest_runs",
        help_text="Versions that are requested for ingest in this run",
    )

    @transition(field=state, source="waiting", target="running")
    def start(self):
        """ Begin running the ingest process """
        return

    @transition(field=state, source="running", target="complete")
    def complete(self):
        """ Finish running the ingest process without error """
        return

    @transition(field=state, source="*", target="canceled")
    def cancel(self):
        """
        Cancel the ingest run on request from the user or on account of a new
        ingest run being started for the same input parameters
        """
        return

    @transition(field=state, source="*", target="failed")
    def fail(self):
        """ Fail the ingest run due to a problem that prevented completion """
        return


@receiver(post_save, sender=IngestRun)
def set_input_hash(sender, instance, **kwargs):
    """
    Create a hash for the versions by concatenating their kf_ids

    NB: This probably will only work if we call save() again after the
    version relationships have been added.
    Adding relationships with the versions won't trigger save() or the save
    signal afaik.
    """
    ids = "".join(v.kf_id for v in instance.versions.all())
    md5hash = hashlib.md5(ids.encode())
    instance.input_hash = hashlib.md5.new(ids).digest()
