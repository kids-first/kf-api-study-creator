import logging
import django_rq
from django.conf import settings
from django.contrib.auth import get_user_model

from creator.decorators import task
from creator.releases.models import ReleaseTask
from creator.count_service.models import CountTask

logger = logging.getLogger(__name__)


@task("task", related_models={ReleaseTask: "task_id"})
def run(task_id=None):
    logger.info("Entering service's context")
    try:
        count_task = CountTask.objects.get(pk=task.pk)
    except CountTask.DoesNotExist:
        raise HttpResponseBadRequest("The specified task does not exist")

    count_task.stage()
    count_task.save()


@task("task", related_models={ReleaseTask: "task_id"})
def publish(release_id=None):
    logger.info("Entering service's context")
    try:
        count_task = CountTask.objects.get(pk=task.pk)
    except CountTask.DoesNotExist:
        raise HttpResponseBadRequest("The specified task does not exist")

    count_task.complete()
    count_task.save()
