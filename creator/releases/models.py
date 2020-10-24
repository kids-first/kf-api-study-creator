import uuid
import requests
import logging
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django_fsm import FSMField, transition
from semantic_version import Version
from semantic_version.django_fields import VersionField

from creator.authentication import service_headers
from creator.fields import kf_id_generator
from creator.studies.models import Study
from creator.jobs.models import JobLog

logger = logging.getLogger(__name__)

User = get_user_model()

FAIL_SOURCES = [
    "waiting",
    "initializing",
    "running",
    "staged",
    "publishing",
    "canceling",
]


def release_id():
    return kf_id_generator("RE")


def task_id():
    return kf_id_generator("TA")


def task_service_id():
    return kf_id_generator("TS")


def next_version(major=False, minor=False, patch=True):
    """
    Assign the next version by taking the version of the last release and
    bumping the patch number by one
    """
    try:
        r = Release.objects.latest()
    except Release.DoesNotExist:
        return Version("0.0.0")

    v = r.version
    if major:
        v = v.next_major()
    elif minor:
        v = v.next_minor()
    else:
        v = v.next_patch()
    return v


class Release(models.Model):
    """
    A release contains a set of studies which are operated on by a list of
    tasks.
    """

    class Meta:
        permissions = [
            ("list_all_release", "Show all releases"),
            ("publish_release", "Publish a release"),
            ("cancel_release", "Cancel a release"),
        ]
        get_latest_by = "created_at"

    kf_id = models.CharField(
        max_length=11,
        primary_key=True,
        default=release_id,
        help_text="Kids First ID assigned to the release",
    )
    uuid = models.UUIDField(
        default=uuid.uuid4, help_text="UUID used internally"
    )
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="releases",
        help_text="The user who created the release",
    )
    name = models.CharField(max_length=256, help_text="Name of the release")
    description = models.CharField(
        max_length=5000, blank=True, help_text="Release notes"
    )
    state = FSMField(
        default="waiting", help_text="The current state of the release"
    )
    studies = models.ManyToManyField(
        Study,
        related_name="releases",
        help_text="kf_ids of the studies " "in this release",
    )
    version = VersionField(
        partial=False,
        coerce=False,
        default=next_version,
        help_text="Semantic version of the release",
    )
    is_major = models.BooleanField(
        default=False,
        help_text="Whether the release is a major version change or not",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Date created"
    )

    @transition(field=state, source="waiting", target="initializing")
    def initialize(self):
        """ Begin initializing tasks """
        return

    @transition(field=state, source="initializing", target="running")
    def start(self):
        """ Start the release """
        return

    @transition(field=state, source="running", target="staged")
    def staged(self):
        """ The release has been staged """
        return

    @transition(field=state, source="staged", target="publishing")
    def publish(self):
        """ Start publishing the release """
        return

    @transition(field=state, source="publishing", target="published")
    def complete(self):
        """ Complete publishing """
        if self.is_major:
            self.version = self.version.next_major()
        else:
            self.version = self.version.next_minor()
        self.save()
        return

    @transition(field=state, source=FAIL_SOURCES, target="canceling")
    def cancel(self):
        """ Cancel the release """
        return

    @transition(field=state, source="canceling", target="canceled")
    def canceled(self):
        """ The release has finished canceling """
        return

    @transition(field=state, source=FAIL_SOURCES, target="failed")
    def failed(self):
        """ The release failed """
        return


class ReleaseTask(models.Model):
    """
    A Release Task is a process that is run on a Task Service as part of a
    Release.
    """

    class Meta:
        permissions = [("list_all_releasetask", "Show all release tasks")]
        get_latest_by = "created_at"

    kf_id = models.CharField(max_length=11, primary_key=True, default=task_id)
    uuid = models.UUIDField(
        default=uuid.uuid4, help_text="UUID used internally"
    )
    state = FSMField(
        default="waiting", help_text="The current state of the task"
    )
    progress = models.IntegerField(
        default=0,
        help_text="Optional field"
        " representing what percentage of the task"
        " has been completed",
    )
    release = models.ForeignKey(
        Release,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="tasks",
    )
    release_service = models.ForeignKey(
        "ReleaseService",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="tasks",
    )
    job_log = models.ForeignKey(
        JobLog,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="job_log",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Time the task was created"
    )

    def _send_action(self, action):
        """
        Send a request to the task's service with a specified command and
        return the json content of the response.
        """

        headers = service_headers()

        body = {
            "action": action,
            "task_id": self.kf_id,
            "release_id": self.release.kf_id,
        }

        logger.info(f"Sending action to {self.release_service.url}: {body}")
        try:
            resp = requests.post(
                self.release_service.url + "/tasks",
                headers=headers,
                json=body,
                timeout=settings.REQUESTS_TIMEOUT,
            )
            logger.info(
                f"Recieved response from {self.release_service.url}: "
                f"{resp.json()}"
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as err:
            logger.error(f"problem requesting task for publish: {err}")
            raise err

        state = resp.json()
        # Check that we recieved the state for correct task
        # Otherwise, we should ignore this response and raise an error
        if (
            state["task_id"] != self.kf_id
            or state["release_id"] != self.release.kf_id
        ):
            error = "Recieved a response that did not match the expected task"
            logger.error(error)
            raise ValueError(error)

        return state

    @transition(field=state, source="waiting", target="initialized")
    def initialize(self):
        """
        Sends the initialize command to the task's service.
        """
        state = self._send_action("initialize")

        task_state = state["state"]

        if task_state not in ["initialized"]:
            error = (
                f"Recieved invalid state '{task_state}' for task "
                f"'{self.kf_id}'. Expected to recieve 'initialized' state."
            )
            logger.error(error)
            raise ValueError(error)

    @transition(field=state, source="initialized", target="running")
    def start(self):
        """
        Sends the start command to the task's service.
        """
        state = self._send_action("start")

        task_state = state["state"]

        if task_state not in ["running"]:
            error = (
                f"Recieved invalid state '{task_state}' for task "
                f"'{self.kf_id}'. Expected to recieve 'running' state."
            )
            logger.error(error)
            raise ValueError(error)

    @transition(field=state, source="running", target="staged")
    def stage(self):
        return

    @transition(field=state, source="staged", target="publishing")
    def publish(self):
        """
        Sends the publish command to the task's service.
        """
        state = self._send_action("publish")

        task_state = state["state"]

        if task_state != "publishing":
            error = (
                f"Recieved invalid state '{task_state}' for task "
                "'{self.kf_id}'. Expected to recieve 'publishing' state."
            )
            logger.error(error)
            raise ValueError(error)

    @transition(field=state, source="publishing", target="published")
    def complete(self):
        return

    @transition(field=state, source="waiting", target="rejected")
    def reject(self):
        return

    @transition(field=state, source="*", target="failed")
    def failed(self):
        return

    @transition(field=state, source="*", target="canceled")
    def cancel(self):
        """
        Sends the cancel command to the task's service.
        """
        state = self._send_action("cancel")

        task_state = state["state"]

        if task_state not in ["canceling"]:
            error = (
                f"Recieved invalid state '{task_state}' for task "
                f"'{self.kf_id}'. Expected to recieve 'canceling' state."
            )
            logger.error(error)
            raise ValueError(error)


class ReleaseService(models.Model):
    """
    A Release Service runs a particular Task that is required for a release
    """

    class Meta:
        permissions = [
            ("list_all_releaseservice", "Show all release services")
        ]
        get_latest_by = "created_at"

    kf_id = models.CharField(
        max_length=11,
        primary_key=True,
        default=task_service_id,
        help_text="Kids First ID assigned to the service",
    )
    uuid = models.UUIDField(
        default=uuid.uuid4, help_text="UUID used internally"
    )
    name = models.CharField(
        max_length=100, help_text="The name of the service"
    )
    description = models.CharField(
        max_length=500, help_text="Description of the service's" "function"
    )
    url = models.CharField(
        max_length=200, help_text="endpoint for the service's API"
    )
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="services",
        help_text="The user who created the service",
    )
    last_ok_status = models.IntegerField(
        default=0,
        help_text="number of pings since last"
        " 200 response from the task's "
        " /status endpoint",
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Whether to run the task as part " "of a release.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Time the task was created"
    )
