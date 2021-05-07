import hashlib
import uuid
import re

from django.utils import timezone
import django_rq
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django_fsm import FSMField, transition

from creator.jobs.models import JobLog
from creator.utils import stop_job

User = get_user_model()


def camel_to_snake(camel_str):
    """
    Convert CamelCase to snake_case
    """
    return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()


def hash_versions(version_kf_ids):
    """
    Uniquely identify a set of file Versions by computing an MD5 hash digest
    using the primary keys of the Versions
    """
    version_id_str = "".join(sorted(v for v in version_kf_ids))
    return hashlib.md5(version_id_str.encode("utf-8")).hexdigest()


class State(object):
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    RUNNING = "running"
    FAILED = "failed"
    CANCELING = "canceling"
    CANCELED = "canceled"
    COMPLETED = "completed"


FAIL_SOURCES = [
    State.NOT_STARTED,
    State.INITIALIZING,
    State.RUNNING,
    State.CANCELING,
]
CANCEL_SOURCES = [
    State.NOT_STARTED,
    State.INITIALIZING,
    State.RUNNING,
]


class IngestProcess(models.Model):
    """
    Common model functionality for ingest processes
    (e.g. ingest run, validation run)
    """
    __queue__ = settings.INGEST_QUEUE

    class Meta:
        abstract = True

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Time when the ingest process was created",
    )
    started_at = models.DateTimeField(
        null=True,
        help_text="Time when ingest process started running"
    )
    stopped_at = models.DateTimeField(
        null=True,
        help_text="Time when ingest process stopped running"
    )
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="%(class)ss",
        related_query_name="%(class)s",
        on_delete=models.SET_NULL,
        help_text="The user who submitted this ingest process",
    )
    input_hash = models.UUIDField(
        null=True,
        blank=True,
        editable=False,
        help_text=(
            "Identifies an ingest process execution by its input parameters. "
            "Autopopulated on save with the MD5 hash of all of the "
            "ingest process input parameters."
        ),
    )
    state = FSMField(
        default=State.NOT_STARTED,
        help_text="The current state of the ingest process"
    )
    job_log = models.OneToOneField(
        JobLog,
        null=True,
        blank=True,
        related_name="%(class)s",
        related_query_name="%(class)s",
        on_delete=models.CASCADE,
        help_text=(
            "The associated job log detailing the execution "
            "for this ingest process"
        ),
    )

    @property
    def queue(self):
        """
        Return a reference to the ingest queue.
        """
        return django_rq.get_queue(name=self.__queue__)

    @transition(
        field=state, source=State.NOT_STARTED, target=State.INITIALIZING
    )
    def initialize(self):
        """
        Begin initializing the ingest process.
        """
        self.started_at = timezone.now()
        self._save_event(State.INITIALIZING)

    @transition(
        field=state, source=State.INITIALIZING, target=State.RUNNING
    )
    def start(self):
        """
        Begin running the ingest process.
        """
        self._save_event(State.RUNNING)

    @transition(field=state, source=State.RUNNING, target=State.COMPLETED)
    def complete(self):
        """
        Finish running the ingest process without error.
        """
        self.stopped_at = timezone.now()
        self._save_event(State.COMPLETED)

    @transition(field=state, source=CANCEL_SOURCES, target=State.CANCELING)
    def start_cancel(self, on_delete=False):
        """
        Start the cancellation of an ingest process on request from the user
        or on account of a new ingest process being started for the same
        input parameters.
        """
        self._save_event(State.CANCELING, on_delete=on_delete)

    @transition(field=state, source=[State.CANCELING], target=State.CANCELED)
    def cancel(self, on_delete=False):
        """
        Complete cancellation of the ingest process
        """
        self.stopped_at = timezone.now()
        stop_job(str(self.pk), queue=self.queue, delete=True)
        self._save_event(State.CANCELED, on_delete=on_delete)

    @transition(field=state, source=FAIL_SOURCES, target=State.FAILED)
    def fail(self):
        """
        Fail the ingest process due to a problem that prevented completion.
        """
        self.stopped_at = timezone.now()
        self._save_event(State.FAILED)

    def compute_input_hash(self):
        """
        Compute an MD5 hash digest from the ingest processes input parameters:
        - List of file version ids (Version.kf_id)

        This will be used to determine whether an ingest process is already
        running for a set of file versions
        """
        return hash_versions(
            self.versions.values_list("pk", flat=True)
        )

    def _save_event(self, event_type, on_delete=False):
        """
        Create and save an event for an ingest process state transition

        If on_delete=True then don't include a ref to the object in the event
        since it may not exist
        """

        from creator.events.models import Event
        snake_name = camel_to_snake(self.__class__.__name__)
        name = camel_to_snake(self.__class__.__name__).replace("_", " ")
        prefix = "".join([w[0] for w in snake_name.split("_")]).upper()
        msgs = {
            State.INITIALIZING: (
                f"{prefix}_INI",
                f"{self.creator.username} started {name} {self.pk}"
            ),
            State.RUNNING: (
                f"{prefix}_STA",
                f"{name.title()} {self.pk} is running"
            ),
            State.COMPLETED: (
                f"{prefix}_COM",
                f"{name.title()} {self.pk} completed"
            ),
            State.CANCELING: (
                f"{prefix}_CLG",
                f"{self.creator.username} requested to cancel {name} {self.pk}"
            ),
            State.CANCELED: (
                f"{prefix}_CAN",
                f"{name.title()} {self.pk} is canceled"
            ),
            State.FAILED: (
                f"{prefix}_FAI",
                f"{name.title()} {self.pk} failed"
            ),
        }
        event_name, message = msgs[event_type]
        kwargs = {
            "study": self.study,
            "user": self.creator,
            "description": message,
            "event_type": event_name,
        }
        if not on_delete:
            kwargs[snake_name] = self

        return Event(**kwargs).save()
