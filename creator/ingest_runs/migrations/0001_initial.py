# Generated by Django 2.2.13 on 2020-11-09 22:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("files", "0022_add_genomic_workflow_output_type"),
        ("jobs", "0001_move_jobs"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IngestRun",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "input_hash",
                    models.UUIDField(
                        blank=True,
                        editable=False,
                        help_text="Identifies an ingest run by its input parameters. Autopopulated on save with the MD5 hash of all of the ingest run input parameters.",
                        null=True,
                    ),
                ),
                (
                    "name",
                    models.TextField(
                        blank=True,
                        help_text="The name of the ingest run. Autopopulated on save with the concatenation of the IngestRun's file version IDs",
                        null=True,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Time when the ingest run was created",
                        null=True,
                    ),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        blank=True,
                        help_text="The user who submitted this ingest run",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ingest_runs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "job_log",
                    models.OneToOneField(
                        blank=True,
                        help_text="The associated job log detailing the execution for this ingest run",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="job_log",
                        to="jobs.JobLog",
                    ),
                ),
                (
                    "versions",
                    models.ManyToManyField(
                        help_text="List of files to ingest in the ingest run",
                        related_name="ingest_runs",
                        to="files.Version",
                    ),
                ),
            ],
            options={
                "permissions": [
                    ("list_all_ingestrun", "Show all ingest_runs"),
                    ("cancel_ingestrun", "Cancel an ingest_run"),
                ],
            },
        ),
    ]
