import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django_fsm import FSMField
from semantic_version import Version
from semantic_version.django_fields import VersionField

from creator.fields import kf_id_generator
from creator.studies.models import Study
from creator.jobs.models import JobLog

User = get_user_model()


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
        permissions = [("list_all_release", "Show all releases")]
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
