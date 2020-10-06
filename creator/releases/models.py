import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django_fsm import FSMField
from semantic_version import Version
from semantic_version.django_fields import VersionField

from creator.fields import kf_id_generator
from creator.studies.models import Study

User = get_user_model()


def release_id():
    return kf_id_generator("RE")()


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
