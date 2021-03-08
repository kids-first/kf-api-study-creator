import json
import logging
import django_rq
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from creator.releases.models import Release, ReleaseTask
from creator.count_service.models import CountTask
from creator.count_service.tasks import run, publish


logger = logging.getLogger(__name__)


def status(request):
    response = JsonResponse({"name": "Diffing Service", "version": "1.0.0"})
    return response


def parse_request(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception as err:
        return HttpResponseBadRequest(f"Problem parsing request: {err}")

    if (
        data is None
        or "action" not in data
        or "task_id" not in data
        or "release_id" not in data
        or "studies" not in data
    ):
        return HttpResponseBadRequest(
            "A JSON payload including 'action', 'task_id', "
            "'release_id', and 'studies' is required"
        )

    action = data["action"]
    task_id = data["task_id"]
    release_id = data["release_id"]

    if not action in [
        "initialize",
        "start",
        "publish",
        "get_status",
        "cancel",
    ]:
        return HttpResponseBadRequest(
            "The action must be specified as one of 'initialize', "
            "'start', 'publish', 'get_status', 'cancel'"
        )

    try:
        task = ReleaseTask.objects.get(pk=task_id)
    except ReleaseTask.DoesNotExist:
        return HttpResponseBadRequest("The specified task does not exist")

    try:
        release = Release.objects.get(pk=release_id)
    except Release.DoesNotExist:
        return HttpResponseBadRequest("The specified release does not exist")

    return action, task, release


@csrf_exempt
@require_http_methods(["GET", "POST"])
def tasks(request):
    """
    Process one of the requested actions
    """
    action, task, release = parse_request(request)

    logger.info(f"{action} {task} {release}")

    if action == "initialize":
        count_task = CountTask(pk=task.pk)
        count_task.save()
    else:
        try:
            count_task = CountTask.objects.get(pk=task.pk)
        except CountTask.DoesNotExist:
            raise HttpResponseBadRequest("The specified task does not exist")

    if action == "start":
        count_task.start()
        count_task.save()
        try:

            queue = django_rq.get_queue("releases")
            queue.enqueue(
                run, task_id=count_task.pk, ttl=settings.RQ_DEFAULT_TTL
            )
        except Exception as err:
            logger.error(err)

    if action == "publish":
        count_task.publish()
        count_task.save()

        queue = django_rq.get_queue("releases")
        queue.enqueue(
            publish, task_id=count_task.pk, ttl=settings.RQ_DEFAULT_TTL
        )

    if action == "cancel":
        count_task.cancel()
        count_task.save()

    response = JsonResponse(
        {
            "state": count_task.state,
            "release_id": release.pk,
            "task_id": count_task.pk,
            "progress": 0,
        }
    )
    return response
