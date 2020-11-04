from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_fsm.signals import post_transition

from creator.releases.models import Release, ReleaseTask, ReleaseEvent
from creator.releases.models import ReleaseEvent
from creator.releases.slack import send_status_notification


@receiver(post_transition, sender=Release)
def create_release_event(sender, instance, name, source, target, **kwargs):
    """
    Create a new event whenever a release transitions states
    """
    ev_type = "error" if target in ["failed", "rejected"] else "info"
    ev = ReleaseEvent(
        event_type=ev_type,
        message="release {}, version {} changed from {} to {}".format(
            instance.kf_id, instance.version, source, target
        ),
        release=instance,
    )
    ev.save()


@receiver(post_transition, sender=ReleaseTask)
def create_task_event(sender, instance, name, source, target, **kwargs):
    """
    Create a new event whenever a task transitions states
    """
    ev_type = "error" if target in ["failed", "rejected"] else "info"
    ev = ReleaseEvent(
        event_type=ev_type,
        message="task {} changed from {} to {}".format(
            instance.kf_id, source, target
        ),
        release=instance.release,
        task=instance,
        release_service=instance.release_service,
    )
    ev.save()


@receiver(post_save, sender=ReleaseEvent)
def send_slack_notification(sender, instance, **kwargs):
    """
    Send a slack notification whenever an event occurs
    """
    if instance.task or instance.release_service:
        return

    if instance.release.state in ["waiting", "initializing"]:
        return

    send_status_notification(instance.release.pk)
