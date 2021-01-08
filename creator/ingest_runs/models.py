import hashlib
import django_rq
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django_fsm import FSMField, transition

from creator.files.models import Version
from creator.jobs.models import JobLog
from creator.utils import stop_job

DELIMITER = "-"
NAME_PREFIX = "INGEST_RUN"
INGEST_QUEUE_NAME = "ingest"

User = get_user_model()


class IngestRun(models.Model):
    """
    Request to ingest file(s) into a target data service
    """

    class Meta:
        permissions = [
            ("list_all_ingestrun", "Show all ingest_runs"),
            ("cancel_ingestrun", "Cancel an ingest_run"),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    input_hash = models.UUIDField(
        null=True,
        blank=True,
        editable=False,
        help_text=(
            "Identifies an ingest run by its input parameters. Autopopulated "
            "on save with the MD5 hash of all of the ingest run "
            "input parameters."
        ),
    )

    name = models.TextField(
        blank=True,
        null=True,
        help_text=(
            "The name of the ingest run. Autopopulated on save with the "
            "concatenation of the IngestRun's file version IDs"
        ),
    )

    versions = models.ManyToManyField(
        Version,
        related_name="ingest_runs",
        help_text="List of files to ingest in the ingest run",
    )

    job_log = models.OneToOneField(
        JobLog,
        null=True,
        blank=True,
        related_name="job_log",
        on_delete=models.CASCADE,
        help_text=(
            "The associated job log detailing the execution "
            "for this ingest run"
        ),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Time when the ingest run was created",
    )

    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="ingest_runs",
        on_delete=models.SET_NULL,
        help_text="The user who submitted this ingest run",
    )

    state = FSMField(
        default="waiting", help_text="The current state of the ingest run"
    )

    @transition(field=state, source="waiting", target="started")
    def start(self):
        """
        Begin running the ingest process.
        """
        return

    @transition(field=state, source="started", target="completed")
    def complete(self):
        """
        Finish running the ingest process without error.
        """
        return

    @transition(field=state, source=["started", "waiting"], target="canceled")
    def cancel(self):
        """
        Cancel the ingest run on request from the user or on account of a new
        ingest run being started for the same input parameters.
        """
        stop_job(str(self.id), queue=self.queue, delete=True)

    @transition(
        field=state, source=["started", "canceled", "waiting"], target="failed"
    )
    def fail(self):
        """
        Fail the ingest run due to a problem that prevented completion.
        """
        return

    def compute_input_hash(self, versions=None):
        """
        Compute an MD5 hash digest from the IngestRun's input parameters:
            - List of file version ids (Version.kf_id)
        """
        versions = versions or self.versions.all()
        version_id_str = "".join(sorted(v.kf_id for v in versions))
        return hashlib.md5(version_id_str.encode("utf-8")).hexdigest()

    def compute_name(self):
        """
        Compute the name from the IngestRun's file version ids
        """
        version_id_str = DELIMITER.join(
            sorted(v.kf_id for v in self.versions.all())
        )
        return DELIMITER.join([NAME_PREFIX, version_id_str])

    @property
    def queue(self):
        """
        Return a reference to the ingest queue.
        """
        return django_rq.get_queue(name=INGEST_QUEUE_NAME)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return str(self.id)
