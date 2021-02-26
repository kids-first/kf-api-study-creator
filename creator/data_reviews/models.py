import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django_fsm import FSMField, transition

from creator.fields import kf_id_generator
from creator.studies.models import Study
from creator.files.models import Version

User = get_user_model()


def data_review_id():
    return kf_id_generator("DR")


class State(object):
    NOT_STARTED = "not_started"
    IN_REVIEW = "in_review"
    WAITING = "awaiting_updates"
    COMPLETED = "completed"
    CLOSED = "closed"


class DataReview(models.Model):
    """
    The iterative process between a data contributor and the Data Resource
    Center where study data is continually supplied, validated, and refined
    to meet quality standards.
    """

    class Meta:
        permissions = [
            ("list_all_datareview", "Show all data_reviews"),
        ]

    kf_id = models.CharField(
        max_length=11,
        primary_key=True,
        default=data_review_id,
        help_text="Kids First ID assigned to the data review",
    )
    uuid = models.UUIDField(
        default=uuid.uuid4, help_text="UUID used internally"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Time when the data_review was created",
    )
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="data_reviews",
        help_text="The user who created the data review",
    )
    name = models.CharField(
        max_length=256, help_text="Name of the data review"
    )
    description = models.TextField(
        max_length=10000,
        null=True,
        blank=True,
        help_text="Description of data review",
    )
    state = FSMField(
        default=State.NOT_STARTED,
        help_text="The current state of the data review",
    )
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE,
        null=True,
        related_name="data_reviews",
    )
    versions = models.ManyToManyField(
        Version,
        related_name="data_reviews",
        help_text="kf_ids of the file versions in this data review",
    )

    @transition(field=state, source=State.NOT_STARTED, target=State.IN_REVIEW)
    def start(self):
        """ Start the data review """

        self._save_event(
            "DR_STA",
            f"{self.creator.username} started a data review",
        )

    @transition(field=state, source=State.IN_REVIEW, target=State.WAITING)
    def wait_for_updates(self):
        """ Feedback was sent to data contributors, now wait for updates """

        self._save_event(
            "DR_WAI",
            "Data review is waiting for updates",
        )

    @transition(field=state, source=State.WAITING, target=State.IN_REVIEW)
    def receive_updates(self):
        """ Receive and process updates to data review """

        self._save_event(
            "DR_UPD",
            "Data review received file updates",
        )

    @transition(field=state, source=State.IN_REVIEW, target=State.COMPLETED)
    def approve(self):
        """ Approve/complete the data review """

        self._save_event(
            "DR_APP",
            f"{self.creator.username} completed the data review",
        )

    @transition(
        field=state,
        source=[State.NOT_STARTED, State.IN_REVIEW, State.WAITING],
        target=State.CLOSED,
    )
    def close(self):
        """ Close the data review before it is completed """

        self._save_event(
            "DR_CLO",
            f"{self.creator.username} closed the data review",
        )

    @transition(field=state, source=State.CLOSED, target=State.IN_REVIEW)
    def reopen(self):
        """ Re-open a closed data review """

        self._save_event(
            "DR_REO",
            f"{self.creator.username} re-opened the data review",
        )

    def _save_event(self, event_type, message):
        """ Create and save an event for a data review state transition """

        from creator.events.models import Event

        return Event(
            study=self.study,
            user=self.creator,
            data_review=self,
            description=message,
            event_type=event_type,
        ).save()
