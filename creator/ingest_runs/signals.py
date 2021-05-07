import django_rq
import logging

from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django_fsm.signals import post_transition

from creator.events.models import Event
from creator.files.models import File, Version
from creator.data_reviews.models import DataReview
from creator.ingest_runs.models import (
    IngestRun,
    ValidationRun,
    State,
    CANCEL_SOURCES,
)
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


@receiver(pre_delete, sender=ValidationRun)
def validation_run_pre_delete(sender, instance, using, *args, **kwargs):
    """
    Fire events and cancel the associated job before deleting the run
    """
    logger.info(
        f"Deleting validation run {instance.pk} and canceling associated jobs"
    )
    instance.start_cancel(on_delete=True)
    instance.cancel(on_delete=True)
    instance.save()


@receiver(pre_delete, sender=IngestRun)
def ingest_run_pre_delete(sender, instance, using, *args, **kwargs):
    """
    Fire events and cancel the associated job before deleting the run
    """
    logger.info(
        f"Deleting ingest run {instance.pk} and canceling associated jobs"
    )
    instance.start_cancel(on_delete=True)
    instance.cancel(on_delete=True)
    instance.save()


def cancel_invalid_ingest_runs(version):
    """
    Cancel all running or waiting to be run IngestRuns involving _version_
    """
    filter_params = {
        "state__in": CANCEL_SOURCES,
        "versions": version
    }
    invalid_ingests = IngestRun.objects.filter(**filter_params).all()
    for ingest in invalid_ingests:
        # Transition to canceling state
        ingest.start_cancel()
        ingest.save()
        django_rq.enqueue(cancel_ingest, ingest.id)


def cancel_invalid_validation_runs(version):
    """
    Cancel all currently running or waiting to be run ValidationRuns
    involving _version_
    """
    filter_params = {
        "state__in": CANCEL_SOURCES,
        "data_review__versions": version
    }
    invalid_runs = (
        ValidationRun.objects
        .select_related("data_review")
        .filter(**filter_params)
        .distinct()
    )
    for run in invalid_runs:
        # Transition to canceling state
        run.start_cancel()
        run.save()
        django_rq.enqueue(cancel_validation, str(run.id))
