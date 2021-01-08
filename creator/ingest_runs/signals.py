import django_rq
import logging

from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django_fsm.signals import post_transition

from creator.events.models import Event
from creator.files.models import File, Version
from creator.ingest_runs.models import IngestRun
from creator.ingest_runs.tasks import cancel_ingest


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


@receiver(pre_delete, sender=Version)
def version_pre_delete(sender, instance, using, *args, **kwargs):
    """
    When a Version is deleted, cancel any IngestRuns
    that include this Version.
    """
    logging.info(
        f"Canceling all ingest runs containing version {instance.pk} before"
        f" its deletion."
    )
    cancel_invalid_ingest_runs(instance)


def cancel_invalid_ingest_runs(version):
    """
    Cancel all currently running IngestRuns that contain _version_ among its
    Versions.
    """
    invalid_ingests = IngestRun.objects.filter(
        state="started", versions=version
    ).all()
    for ingest in invalid_ingests:
        django_rq.enqueue(cancel_ingest, ingest.id)


@receiver(post_transition, sender=IngestRun)
def ingest_run_post_transition(
    sender, instance, name, source, target, *args, **kwargs
):
    """
    Create a corresponding Event after the status of an IngestRun is changed.
    """
    TARGET_EVENT_TYPES = {
        "started": "IR_STA",
        "completed": "IR_COM",
        "canceled": "IR_CAN",
        "failed": "IR_FAI",
    }
    versions = [str(v) for v in instance.versions.all()]
    started_by_user = target in {"started", "canceled"}
    if not started_by_user:
        message = (
            f"IngestRun {instance.pk} {target} for file versions {versions} "
        )
    else:
        message = (
            f"{instance.creator.display_name} {target} IngestRun "
            f"{instance.pk} for file versions {versions} "
        )
    first_version = instance.versions.first()
    ev = Event(
        study=first_version.study,
        file=first_version.root_file,
        version=first_version,
        user=instance.creator,
        description=message,
        event_type=TARGET_EVENT_TYPES[target],
    )
    ev.save()
