import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from creator.studies.models import Study
from creator.organizations.models import Organization
from creator.files.models import File, Version
from creator.projects.models import Project
from creator.buckets.models import Bucket
from creator.data_reviews.models import DataReview
from creator.ingest_runs.models import IngestRun, ValidationRun

User = get_user_model()


class Event(models.Model):
    """
    An Event that involved some user, study, file, version, or a combination
    of them.
    """

    class Meta:
        permissions = [
            (
                "view_my_event",
                "Can view all events in studies user is a member of",
            )
        ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(
        default=timezone.now,
        null=False,
        help_text="Time the event was created",
    )
    event_type = models.CharField(
        max_length=6,
        choices=(
            ("VR_INI", "Validation Run Initializing"),
            ("VR_STA", "Validation Run Started"),
            ("VR_CLG", "Validation Run Canceling"),
            ("VR_CAN", "Validation Run Canceled"),
            ("VR_COM", "Validation Run Completed"),
            ("VR_FAI", "Validation Run Failed"),
            ("IR_INI", "Ingest Run Initializing"),
            ("IR_STA", "Ingest Run Started"),
            ("IR_CAN", "Ingest Run Canceled"),
            ("IR_CLG", "Ingest Run Canceling"),
            ("IR_COM", "Ingest Run Completed"),
            ("IR_FAI", "Ingest Run Failed"),
            ("SF_CRE", "Study File Created"),
            ("SF_UPD", "Study File Updated"),
            ("SF_DEL", "Study File Deleted"),
            ("FV_CRE", "File Version Created"),
            ("FV_UPD", "File Version Updated"),
            ("SD_CRE", "Study Created"),
            ("SD_UPD", "Study Updated"),
            ("PR_CRE", "Project Created"),
            ("PR_UPD", "Project Updated"),
            ("PR_DEL", "Project Deleted"),
            ("PR_LIN", "Project Linked"),
            ("PR_UNL", "Project Unlinked"),
            ("PR_STR", "Project Creation Start"),
            ("PR_ERR", "Project Creation Error"),
            ("PR_SUC", "Project Creation Success"),
            ("BK_STR", "Bucket Creation Start"),
            ("BK_ERR", "Bucket Creation Error"),
            ("BK_SUC", "Bucket Creation Success"),
            ("BK_LIN", "Bucket Linked"),
            ("BK_UNL", "Bucket Unlinked"),
            ("IM_STR", "File Import Start"),
            ("IM_ERR", "File Import Error"),
            ("IM_SUC", "File Import Success"),
            ("CB_ADD", "Collaborator Added"),
            ("CB_UPD", "Collaborator Updated"),
            ("CB_REM", "Collaborator Removed"),
            ("IN_UPD", "Ingestion Status Updated"),
            ("PH_UPD", "Phenotype Status Updated"),
            ("ST_UPD", "Sequencing Status Updated"),
            ("RT_CRE", "Referral Token Created"),
            ("RT_CLA", "Referral Token Claimed"),
            ("SL_STR", "Slack Channel Creation Start"),
            ("SL_ERR", "Slack Channel Creation Error"),
            ("SL_SUC", "Slack Channel Creation Success"),
            ("DR_STA", "Data Review Started"),
            ("DR_WAI", "Data Review Waiting for Updates"),
            ("DR_UPD", "Data Review Updated"),
            ("DR_APP", "Data Review Approved"),
            ("DR_CLO", "Data Review Closed"),
            ("DR_REO", "Data Review Re-opened"),
            ("OTH", "Other"),
        ),
        default="OTH",
    )
    description = models.TextField(
        blank=True,
        default="",
        max_length=1000,
        help_text="Description of the event",
    )
    organization = models.ForeignKey(
        Organization,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="events",
        help_text="Organization related to this event",
    )
    study = models.ForeignKey(
        Study,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
        help_text="Study related to this event",
    )
    bucket = models.ForeignKey(
        Bucket,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="buckets",
        help_text="Bucket related to this event",
    )
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
        help_text="Project related to this event",
    )
    file = models.ForeignKey(
        File,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
        help_text="File related to this event",
    )
    version = models.ForeignKey(
        Version,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
        help_text="Version related to this event",
    )
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
        help_text="User related to this event",
    )
    data_review = models.ForeignKey(
        DataReview,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
        help_text="Data Review related to this event",
    )
    ingest_run = models.ForeignKey(
        IngestRun,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
        help_text="Ingest Run related to this event",
    )
    validation_run = models.ForeignKey(
        ValidationRun,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
        help_text="Validation Run related to this event",
    )
