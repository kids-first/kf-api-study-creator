from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from creator.files.models import File, Version
from .models import Event


@receiver(post_save, sender=File)
def new_file(signal, sender, instance, created, **kwargs):
    """
    Handle new and updated files
    """
    if created:
        message = f"{instance.creator.username} created file {instance.kf_id}"
        event_type = "SF_CRE"
    else:
        message = f"{instance.creator.username} updated file {instance.kf_id}"
        event_type = "SF_UPD"

    event = Event(
        file=instance,
        study=instance.study,
        user=instance.creator,
        description=message,
        event_type=event_type,
    )
    event.save()


@receiver(post_delete, sender=File)
def delete_file(signal, sender, instance, **kwargs):
    """
    Handle deleted files
    """
    message = f"{instance.creator.username} deleted file {instance.kf_id}"
    event = Event(
        study=instance.study,
        user=instance.creator,
        description=message,
        event_type="SF_DEL",
    )
    event.save()


@receiver(post_save, sender=Version)
def new_version(signal, sender, instance, created, **kwargs):
    """
    Handle new versions and updates
    """
    if created:
        message = (
            f"{instance.creator.username} created version {instance.kf_id}"
            f" of file {instance.root_file.kf_id}"
        )
        event_type = "FV_CRE"
    else:
        message = (
            f"{instance.creator.username} updated version {instance.kf_id}"
            f" of file {instance.root_file.kf_id}"
        )
        event_type = "FV_UPD"

    ev = Event(
        study=instance.root_file.study,
        file=instance.root_file,
        version=instance,
        user=instance.creator,
        description=message,
        event_type=event_type,
    )
    ev.save()
