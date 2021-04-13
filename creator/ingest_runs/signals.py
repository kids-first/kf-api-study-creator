import django_rq
import logging

from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django_fsm.signals import post_transition

from creator.events.models import Event
from creator.files.models import File, Version
from creator.data_reviews.models import DataReview
from creator.ingest_runs.models import IngestRun, State, ValidationRun
from creator.ingest_runs.tasks import cancel_ingest, cancel_validation

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=IngestRun)
def ingest_run_pre_save(sender, instance, *args, **kwargs):
    """
    Set the IngestRun's input_hash from its input parameters and the name
    using the version ids if they exist
    """
    # Populate the input_hash and name from the version IDs
    if instance.versions.count() > 0:
        instance.name = instance.compute_name()
        instance.input_hash = instance.compute_input_hash()


@receiver(pre_save, sender=ValidationRun)
def validation_run_presave(sender, instance, *args, **kwargs):
    """
    Set the ValidationRun's input_hash from its input parameters using the
    version ids if they exist
    """
    if instance.versions.count() > 0:
        instance.input_hash = instance.compute_input_hash()


@receiver(pre_delete, sender=Version)
def version_pre_delete(sender, instance, using, *args, **kwargs):
    """
    When a Version is deleted, cancel any running ingest processes
    that include this Version.
    """
    logger.info(
        f"Canceling all processes containing version {instance.pk} before"
        f" its deletion."
    )
    cancel_invalid_ingest_runs(instance)
    cancel_invalid_validation_runs(instance)


@receiver(pre_delete, sender=DataReview)
def data_review_pre_delete(sender, instance, using, *args, **kwargs):
    """
    When a DataReview is deleted, cancel any running ValidationRuns for the
    review.
    """
    logger.info(
        f"Canceling all validation runs for {instance.pk} before its deletion"
    )
    invalid_runs = (
        ValidationRun.objects.select_related("data_review")
        .only("data_review__versions__kf_id")
        .filter(data_review__kf_id=instance.kf_id).distinct()
    )
    for run in invalid_runs:
        django_rq.enqueue(cancel_validation, str(run.id))


def cancel_invalid_ingest_runs(version):
    """
    Cancel all currently running IngestRuns that contain _version_ among its
    Versions.
    """
    invalid_ingests = IngestRun.objects.filter(
        state=State.RUNNING, versions=version
    ).all()
    for ingest in invalid_ingests:
        django_rq.enqueue(cancel_ingest, ingest.id)


def cancel_invalid_validation_runs(version):
    """
    Cancel all currently running ValidationRuns that involve _version_.
    """
    invalid_runs = (
        ValidationRun.objects
        .select_related("data_review").only("data_review__kf_id")
        .filter(state=State.RUNNING, data_review__versions=version).distinct()
    )
    for run in invalid_runs:
        django_rq.enqueue(cancel_validation, str(run.id))
