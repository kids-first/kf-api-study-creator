from django.db import models


class IngestRun(models.Model):
    """
    Plug the model in here
    """

    class Meta:
        permissions = [
            ("list_all_ingestrun", "Show all ingest_runs"),
        ]

    created_at = models.DateTimeField(
        null=False, help_text="Time when the ingest_run was created"
    )
