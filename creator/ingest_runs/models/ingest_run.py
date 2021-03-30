from django.contrib.auth import get_user_model
from django.db import models

from creator.ingest_runs.common.model import IngestProcess
from creator.files.models import Version

DELIMITER = "-"
NAME_PREFIX = "INGEST_RUN"
INGEST_QUEUE_NAME = "ingest"

User = get_user_model()


class IngestRun(IngestProcess):
    """
    Request to ingest file(s) into a target data service
    """

    class Meta(IngestProcess.Meta):
        permissions = [
            ("list_all_ingestrun", "Show all ingest_runs"),
            ("cancel_ingestrun", "Cancel an ingest_run"),
        ]
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

    @property
    def study(self):
        if self.versions.count() > 0:
            return self.versions.first().root_file.study

    def compute_name(self):
        """
        Compute the name from the IngestRun's file version ids
        """
        version_id_str = DELIMITER.join(
            sorted(v.kf_id for v in self.versions.all())
        )
        return DELIMITER.join([NAME_PREFIX, version_id_str])

    def __str__(self):
        if self.name:
            return self.name
        else:
            return str(self.id)
