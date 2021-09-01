from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save

from creator.events.models import Event
from creator.data_templates.models import DataTemplate, TemplateVersion


@receiver(post_save, sender=DataTemplate)
def data_template_post_save(sender, instance, created, **kwargs):
    """
    Fire an event when a data template is created/updated
    """
    if created:
        verb = "created"
        et = "DT_CRE"
    else:
        verb = "updated"
        et = "DT_UPD"
    username = getattr(instance.creator, "display_name", "Anonymous user")

    Event(
        organization=instance.organization,
        data_template=instance,
        user=instance.creator,
        description=f"{username} {verb} data template {instance.pk}",
        event_type=et,
    ).save()


@receiver(post_save, sender=TemplateVersion)
def template_version_post_save(sender, instance, created, **kwargs):
    """
    Fire an event when a template version is created/updated
    """
    if created:
        verb = "created"
        et = "TV_CRE"
    else:
        verb = "updated"
        et = "TV_UPD"
    username = getattr(instance.creator, "display_name", "Anonymous user")

    Event(
        organization=instance.organization,
        template_version=instance,
        user=instance.creator,
        description=f"{username} {verb} template version {instance.pk}",
        event_type=et,
    ).save()


@receiver(post_delete, sender=DataTemplate)
def data_template_post_delete(sender, instance, using, *args, **kwargs):
    """
    Fire an event when a data template is deleted
    """
    username = getattr(instance.creator, "display_name", "Anonymous user")
    Event(
        organization=instance.organization,
        user=instance.creator,
        description=f"{username} deleted data template {instance.pk}",
        event_type="DT_DEL",
    ).save()


@receiver(post_delete, sender=TemplateVersion)
def template_version_post_delete(sender, instance, using, *args, **kwargs):
    """
    Fire an event when a template version is deleted
    """
    username = getattr(instance.creator, "display_name", "Anonymous user")
    Event(
        organization=instance.organization,
        user=instance.creator,
        description=f"{username} deleted template version {instance.pk}",
        event_type="TV_DEL",
    ).save()
