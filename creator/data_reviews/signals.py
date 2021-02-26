from django.dispatch import receiver
from django.db.models.signals import pre_delete, post_save

from creator.files.models import Version
from creator.events.models import Event
from creator.data_reviews.models import DataReview, State


@receiver(pre_delete, sender=Version)
def file_version_pre_delete(sender, instance, using, *args, **kwargs):
    """
    When a file Version is deleted, update related DataReview states and fire
    Data Review update events

    Scenario 1
    -----------------------------------
    Create Study - fa.v1, fb.v1, fc.v1
    Start DataReview - fa.v1, fb.v1
    Version deleted - fc.v1

    Is version part of any Data Review
    No - do nothing

    Scenario 2 - continuation of 1
    -----------------------------------
    Study - fa.v1, fb.v1
    DataReview - fa.v1, fb.v1
    Version deleted - fa.v1

    Is version part of any Data Review
    Yes - update all related review's state, emit event
    """
    for dr in instance.data_reviews.all():
        if dr.state == State.WAITING:
            dr.receive_updates()
            dr.save()
        Event(
            study=dr.study,
            file=instance.root_file,
            user=dr.creator,
            data_review=dr,
            description=(
                "File version {instance.pk} was deleted from data review "
                f"{dr.pk}"
            ),
            event_type="DR_UPD",
        ).save()


@receiver(post_save, sender=Version)
def file_version_post_save(sender, instance, created, *args, **kwargs):
    """
    When a file Version is created, update the states of the related
    DataReview and fire events

    Scenario 1
    -----------------------------------
    Create Study - fa.v1, fb.v1, fc.v1
    Start DataReview - fa.v1, fb.v1
    Receive new version - fc.v2

    Check if instance.root_file has a version that is part of any Data Review
    No - do nothing

    Scenario 2 - continuation of 1
    -----------------------------------
    Study - fa.v1, fb.v1, fc.v2
    DataReview - fa.v1, fb.v1
    Receive new version - fa.v2

    Check if instance.root_file has a version that is part of any Data Review
    Yes - update all related review's state, emit event
    """
    # Only process new versions with root files
    if (not created) or (not instance.root_file):
        return

    # For non-terminal data reviews involving the root file of the version
    # that was uploaded, update the reviews' state + emit events
    for dr in (
        DataReview.objects.exclude(state__in={State.COMPLETED, State.CLOSED})
        .filter(
            versions__in=Version.objects.filter(root_file=instance.root_file)
        )
        .distinct()
    ):
        if dr.state == State.WAITING:
            dr.receive_updates()
            dr.save()
        Event(
            study=instance.root_file.study,
            file=instance.root_file,
            version=instance,
            user=instance.creator,
            data_review=dr,
            description=(
                f"New version {instance.pk} received for file "
                f"{instance.root_file.pk} which is part of open data "
                f"review {dr.pk}"
            ),
            event_type="DR_UPD",
        ).save()
