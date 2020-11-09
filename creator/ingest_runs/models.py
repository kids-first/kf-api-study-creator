import hashlib
import uuid
from django.db import models
from django.contrib.auth import get_user_model

from creator.files.models import Version
from creator.jobs.models import JobLog

DELIMITER = "-"
NAME_PREFIX = "INGEST_REQUEST"

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
            "The name of the ingest run. An field that is auto populated "
            "by concatenating the IDs of the IngestRun's file versions"
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
            "The associated job log detailing the execution " "for this ingest run"
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

    def compute_input_hash(self):
        """
        Compute an MD5 hash digest from the IngestRun's input parameters:
            - List of file version ids (Version.kf_id)
        """
        version_id_str = "".join(sorted(v.kf_id for v in self.versions.all()))
        return hashlib.md5(version_id_str.encode("utf-8")).hexdigest()

    def compute_name(self):
        """
        Compute the name from the IngestRun's file version ids
        """
        version_id_str = DELIMITER.join(sorted(v.kf_id for v in self.versions.all()))
        return DELIMITER.join([NAME_PREFIX, version_id_str])

    def start_job(self, task, *args, **kwargs):
        """
        Enqueue an ingest task to start an ingest job
        """
        pass

    def cancel_job(self):
        """
        Cancel or stop the associated job if it is running
        This method should be called when:
            - A new IngestRun is saved
            - A file version is deleted and that version is involved in an
              IngestRun with an active job
        """
        pass

    def __str__(self):
        if self.name:
            return self.name
        else:
            return str(self.id)
