import django_rq
import logging

from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django_fsm.signals import post_transition

from creator.events.models import Event
from creator.files.models import File, Version
from creator.ingest_runs.models import IngestRun, State, ValidationRun
from creator.ingest_runs.tasks import cancel_ingest

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
    When a Version is deleted, cancel any IngestRuns
    that include this Version.
    """
    logging.info(
        f"Canceling all processes containing version {instance.pk} before"
        f" its deletion."
    )
    cancel_invalid_ingest_runs(instance)


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
