import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from creator.studies.models import Study
from creator.files.models import File, Version

User = get_user_model()


class Event(models.Model):
    """
    An Event that involved some user, study, file, version, or a combination
    of them.
    """

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(
        default=timezone.now,
        null=False,
        help_text="Time the event was created",
    )
    event_type = models.CharField(
        max_length=6,
        choices=(
            ("SF_CRE", "Study File Created"),
            ("SF_UPD", "Study File Updated"),
            ("SF_DEL", "Study File Deleted"),
            ("FV_CRE", "File Version Created"),
            ("FV_UPD", "File Version Updated"),
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
    study = models.ForeignKey(
        Study,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
        help_text="Study related to this event",
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
