import logging
import requests
import django_rq
from django.conf import settings
from django.contrib.auth import get_user_model

from creator.decorators import task
from creator.studies.models import Study
from creator.releases.models import Release, ReleaseTask, ReleaseService

User = get_user_model()

logger = logging.getLogger(__name__)

ALL_RELEASES = """{
  allReleases {
    edges {
      node {
        id
        kfId
        uuid
        name
        description
        author
        isMajor
        state
        createdAt
        studies {
          edges {
            node {
              id
              kfId
            }
          }
        }
        tasks {
          edges {
            node {
              id
              uuid
              kfId
              state
              progress
              createdAt
              taskService {
                id
                kfId
                uuid
                name
                description
                url
                author
                createdAt
              }
              state
            }
          }
        }
      }
    }
  }
}
"""


@task(job="releases_sync")
def sync_releases_task():
    """
    Synchronize Release Coordinator releases with the Study Creator.
    DeprecationWarning: Will remove this task once all Release Coordinator
        operations are moved to the studdy creator.
    """
    api = settings.COORDINATOR_URL
    logger.info(f"Syncing releases with the Release Coordinator at {api}")

    resp = requests.post(api, json={"query": ALL_RELEASES})

    releases = [n["node"] for n in resp.json()["data"]["allReleases"]["edges"]]
    logger.info(
        f"Retrieved {len(releases)} releases from the Release Coordinator"
    )

    # Create releases if they do not exist
    new_releases = 0
    for r in releases:
        defaults = {
            "uuid": r["uuid"],
            "name": r["name"],
            "description": r["description"],
            "is_major": r["isMajor"],
            "created_at": r["createdAt"],
            "state": r["state"],
        }
        release, created = Release.objects.update_or_create(
            kf_id=r["kfId"], defaults=defaults
        )

        if created or True:
            sync_new_release(release, r)
            new_releases += 1

    logger.info(
        f"Imported {new_releases} new releases from the Release Coordinator"
    )


def sync_new_release(release, query):
    # Add studies if the release did not previously exist
    studies = []
    for study in query["studies"]["edges"]:
        try:
            studies.append(Study.objects.get(pk=study["node"]["kfId"]))
        except Study.DoesNotExist:
            logger.warning(
                f"The study '{study['node']['kfId']}' does not exist. "
                "Will not add to the release."
            )
    release.studies.set(studies)

    # Try to find author by username
    try:
        release.creator = User.objects.get(username=query["author"])
    except User.DoesNotExist:
        pass

    # Register tasks
    tasks = []
    for t in query["tasks"]["edges"]:
        task = t["node"]

        # Get the service or create it
        service = task["taskService"]
        defaults = {
            "uuid": service["uuid"],
            "name": service["name"],
            "description": service["description"],
            "created_at": service["createdAt"],
            "url": service["url"],
        }
        release_service, created = ReleaseService.objects.get_or_create(
            kf_id=service["kfId"], defaults=defaults
        )
        try:
            release_service.creator = User.objects.get(
                username=service["author"]
            )
        except User.DoesNotExist:
            pass

        defaults = {
            "uuid": task["uuid"],
            "created_at": task["createdAt"],
            "state": task["state"],
            "release": release,
            "release_service": release_service,
        }
        release_task, created = ReleaseTask.objects.update_or_create(
            kf_id=task["kfId"], defaults=defaults
        )
        tasks.append(release_task)

    logger.info(
        f"Synced new release '{release.kf_id}' with "
        f"{len(studies)} studies and {len(tasks)} tasks."
    )


def initialize_release(release_id):
    """
    Initializes a release by queueing up jobs to initialize each task in the
    release.
    """
    release = Release.objects.get(pk=release_id)

    if release.tasks.count() == 0:
        logger.info(
            f"No services were requested to run for release '{release.pk}'. "
            f"The release will be automatically moved to the 'running' state."
        )
        release.start()
        release.save()

        django_rq.enqueue(start_release, release.pk)
        return

    logger.info(
        f"Queuing jobs to check that {release.tasks.count()} tasks are "
        f"prepared to start processing release '{release.pk}'"
    )

    for task in release.tasks.all():
        logger.info(
            f"Queuing initialize_task for task '{task.pk}' "
            f"of service '{task.release_service.name}'"
        )
        django_rq.enqueue(initialize_task, task.pk)


def initialize_task(task_id):
    """
    Initializes a task by sending it the initialize command.
    """
    task = ReleaseTask.objects.get(pk=task_id)
    try:
        task.initialize()
        task.save()
    except Exception as err:
        logger.error(
            f"There was a problem trying to initialize the service: {err}"
        )
        logger.info(
            "The release will be canceled as the service was not ready to "
            "start a new release"
        )
        task.reject()
        task.save()

        # task.release.cancel()
        # task.release.save()

        # django_rq.enqueue(cancel_release, task.release.pk)

    # Check if all tasks are initialized now and queue up the release start
    if all([t.state == "initialized" for t in task.release.tasks.all()]):
        logger.info(
            "It looks like all tasks in this release are initialized now. "
            "Queueing start_release"
        )
        task.release.start()
        task.release.save()
        django_rq.enqueue(start_release, task.release.pk)


def start_release(release_id):
    """
    Begin a release by invoking start on all services in the release.
    """
    release = Release.objects.get(pk=release_id)

    if release.tasks.count() == 0:
        logger.info(
            f"No services were requested to run for release '{release.pk}'. "
            f"The release will be automatically moved to the 'staged' state."
        )
        release.staged()
        release.save()
        return

    logger.info(
        f"Queuing jobs to start {release.tasks.count()} tasks for the "
        f"release '{release.pk}'"
    )

    for task in release.tasks.all():
        logger.info(
            f"Queuing start_task for task '{task.pk}' "
            f"of service '{task.release_service.name}'"
        )
        django_rq.enqueue(start_task, task.pk)


def start_task(task_id):
    """
    Starts a task by sending it the start command.
    """
    task = ReleaseTask.objects.get(pk=task_id)
    try:
        task.start()
        task.save()
    except Exception as err:
        logger.error(f"There was a problem trying to start the task: {err}")
        logger.info(
            "The release will be canceled as the service failed to start a new"
            " task"
        )
        task.failed()
        task.save()

        # task.release.cancel()
        # task.release.save()

        # django_rq.enqueue(cancel_release, task.release.pk)


def publish_release(release_id):
    """
    Publish a release by sending the release action to each service in the
    release.
    """
    logger.info(f"Publishing release {release_id}")

    release = Release.objects.select_related().get(kf_id=release_id)
    tasks = release.tasks.all()

    # If there are no tasks in our release, just push it to the completed state
    # automatically.
    if not tasks:
        logger.info(
            f"No services were requested to run for release '{release.pk}'. "
            f"The release will be automatically moved to the 'staged' state."
        )
        release.complete()
        release.save()
        return

    # Iterate through each task sequentially and tell it to publish
    for task in tasks:
        logger.info(
            f"Queuing publish_task for task '{task.pk}' "
            f"of service '{task.release_service.name}'"
        )
        django_rq.enqueue(publish_task, task.pk)


def publish_task(task_id):
    """
    Publish a task by sending it the publish command.
    """
    task = ReleaseTask.objects.get(pk=task_id)
    try:
        task.publish()
        task.save()
    except Exception as err:
        logger.error(f"There was a problem trying to publish the task: {err}")
        logger.warn(
            "The release will be canceled as the service failed to publish "
            "the task. Be cautious of undesired end states as some other "
            "tasks may have published their data!"
        )
        task.failed()
        task.save()

        # task.release.cancel()
        # task.release.save()

        # django_rq.enqueue(cancel_release, task.release.pk)
