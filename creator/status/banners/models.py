import datetime
import uuid

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Banner(models.Model):
    """
    An admin defined message to that will be displayed on Data Tracker in order
    to notify Data Tracker users of any new features, changes, or problems.
    """

    class Meta:
        permissions = [
            ("list_all_banner", "Show all banner"),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Time when the banner was created",
    )
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="banners",
        on_delete=models.SET_NULL,
        help_text="The user who submitted this ingest run",
    )
    enabled = models.BooleanField(
        default=False,
        help_text="Whether to display the banner or not"
    )
    start_date = models.DateTimeField(
        default=datetime.datetime.now,
        null=True,
        help_text="When to start displaying the banner",
    )
    end_date = models.DateTimeField(
        default=datetime.datetime.now,
        null=True,
        help_text="When to stop displaying the banner",
    )
    message = models.TextField(
        max_length=1000,
        help_text="The message content for the banner",
    )
    url = models.URLField(
        null=True,
        blank=True,
        help_text="A URL that may be included in the Banner's message as an "
        "HTML <a> element, pointing to additional information about message."
    )
    url_label = models.CharField(
        null=True,
        blank=True,
        max_length=200,
        help_text="A text label meant to be used as a part of the <a> element "
        "containing the Banner url."
    )
    SEVERITY_CHOICES = (
        ("INFO", "Info"),
        ("WARN", "Warning"),
        ("ERROR", "Error"),
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default="INFO",
        help_text="The severity of the message"
    )
