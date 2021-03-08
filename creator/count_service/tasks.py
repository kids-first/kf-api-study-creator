import logging
import django_rq
from django.conf import settings
from django.contrib.auth import get_user_model

from creator.decorators import task
from creator.releases.models import ReleaseTask
from creator.count_service.models import CountTask, StudySummary

import requests

logger = logging.getLogger(__name__)


def create_summary_counts(study):
    """
    Create summary counts for a given study
    """

    entities = ["participants", "biospecimens", "genomic-files"]
    counts = {}
    for entity in entities:
        url = f"{settings.DATASERVICE_URL}/{entity}?study_id={study.kf_id}&limit=1"
        resp = requests.get(url)
        try:
            total = resp.json()["total"]
        except (KeyError) as err:
            logger.warning("Error fetching request from dataservice: {err}")
            continue
        counts[entity] = total
    logger.info(counts)
    return counts


@task("task", related_models={ReleaseTask: "task_id"})
def run(task_id=None):
    logger.info("Entering service's context")
    try:
        count_task = CountTask.objects.get(pk=task_id)
    except CountTask.DoesNotExist:
        logger.warning("The specified task does not exist")
        return

    logger.info("doing stuff")

    for study in count_task.release.studies.all():
        counts = create_summary_counts(study)
        summary = StudySummary(
            count_task=count_task, study=study, counts=counts
        )
        summary.save()

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
