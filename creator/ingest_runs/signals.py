from django.db.models.signals import pre_save
from django.dispatch import receiver
from creator.ingest_runs.models import IngestRun


@receiver(pre_save, sender=IngestRun)
def ingest_run_pre_save(sender, instance, *args, **kwargs):
    """
    Set the IngestRun's input_hash from its input parameters and the name
    using the version ids if they exist
    """
    # Populate the input_hash and name from the version ids
    if instance.versions.count() > 0:
        instance.name = instance.compute_name()
        instance.input_hash = instance.compute_input_hash()


@receiver(post_transition, sender=IngestRun)
def ingest_run_post_transition(sender, instance, name, source, target,
                               *args, **kwargs):
    """
    Create a corresponding Event after the status of an IngestRun is changed.
    """
    TARGET_EVENT_TYPES = {
        "running": "IR_STA",
        "complete": "IR_COM",
        "canceled": "IR_CAN",
        "failed": "IR_FAI",
    }
    username = instance.creator.display_name or "Anonymous user" 
    if target in {"complete", "failed"}:
        message = f"Status change of IngestRun {instance.id} with "
    else:
        message = (
            f"{username} changed the status of IngestRun {instance.id} "
            f"with "
        )
    message + = (
        f"versions {list(instance.versions.all())} to {target.upper()}."
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
