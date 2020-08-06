from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from creator.files.models import File, Version
from .models import Event


@receiver(post_save, sender=File)
def new_file(signal, sender, instance, created, **kwargs):
    """
    Handle new files. Updates are handled directly by the update mutation.
    """
    # Don't do anything for updates
    if not created:
        return
    username = getattr(instance.creator, "display_name", "Anonymous user")
    message = f"{username} created file {instance.kf_id}"

    event = Event(
        file=instance,
        study=instance.study,
        user=instance.creator,
        description=message,
        event_type="SF_CRE",
    )
    event.save()


@receiver(post_delete, sender=File)
def delete_file(signal, sender, instance, **kwargs):
    """
    Handle deleted files
    """
    username = getattr(instance.creator, "display_name", "Anonymous user")
    message = f"{username} deleted file {instance.kf_id}"
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
    username = getattr(instance.creator, "display_name", "Anonymous user")
    if created:
        message = (
            f"{username} created version {instance.kf_id}"
            f" of file {instance.root_file.kf_id}"
        )
        event_type = "FV_CRE"
    else:
        message = (
            f"{username} updated version {instance.kf_id}"
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
