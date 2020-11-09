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
