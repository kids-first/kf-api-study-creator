import logging
import requests
import django_rq
from django.conf import settings
from django.contrib.auth import get_user_model

from creator.authentication import client_headers
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
        version
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
    headers = client_headers(settings.AUTH0_SERVICE_AUD)

    resp = requests.post(api, json={"query": ALL_RELEASES}, headers=headers)

    releases = [n["node"] for n in resp.json()["data"]["allReleases"]["edges"]]
    logger.info(
        f"Retrieved {len(releases)} releases from the Release Coordinator"
    )

    # Create releases if they do not exist
    new_releases = 0
    for r in releases:
        # Don't update releases that are processing
        if r["state"] in ["canceling", "running", "publishing"]:
            continue
        defaults = {
            "uuid": r["uuid"],
            "name": r["name"],
            "version": r["version"],
            "description": r["description"],
            "is_major": r["isMajor"],
            "created_at": r["createdAt"],
            "state": r["state"],
        }
        release, created = Release.objects.update_or_create(
            kf_id=r["kfId"], defaults=defaults
        )

        if created:
            sync_new_release(release, r)
            release.created_at = r["createdAt"]
            release.save()
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


@task("release", related_models={Release: "release_id"})
def initialize_release(release_id=None):
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

        queue = django_rq.get_queue("releases")
        queue.enqueue(
            start_release, release_id=release.pk, ttl=settings.RQ_DEFAULT_TTL
        )
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
        queue = django_rq.get_queue("releases")
        queue.enqueue(
            initialize_task, task_id=task.pk, ttl=settings.RQ_DEFAULT_TTL
        )


@task("release_task", related_models={ReleaseTask: "task_id"})
def initialize_task(task_id=None):
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

        task.release.cancel()
        task.release.save()

        queue = django_rq.get_queue("releases")
        queue.enqueue(
            cancel_release,
            release_id=task.release.pk,
            failed=True,
            ttl=settings.RQ_DEFAULT_TTL,
        )

    # Check if all tasks are pending now and queue up the release start
    if all([t.state == "pending" for t in task.release.tasks.all()]):
        logger.info(
            "It looks like all tasks in this release are pending now. "
            "Queueing start_release"
        )
        task.release.start()
        task.release.save()
        queue = django_rq.get_queue("releases")
        queue.enqueue(
            start_release,
            release_id=task.release.pk,
            ttl=settings.RQ_DEFAULT_TTL,
        )


@task("release", related_models={Release: "release_id"})
def start_release(release_id=None):
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
        queue = django_rq.get_queue("releases")
        queue.enqueue(start_task, task_id=task.pk, ttl=settings.RQ_DEFAULT_TTL)


@task("release_task", related_models={ReleaseTask: "task_id"})
def start_task(task_id=None):
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

        task.release.cancel()
        task.release.save()

        queue = django_rq.get_queue("releases")
        queue.enqueue(
            cancel_release,
            release_id=task.release.pk,
            failed=True,
            ttl=settings.RQ_DEFAULT_TTL,
        )


@task("release", related_models={Release: "release_id"})
def publish_release(release_id=None):
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
        queue = django_rq.get_queue("releases")
        queue.enqueue(
            publish_task, task_id=task.pk, ttl=settings.RQ_DEFAULT_TTL
        )


@task("release_task", related_models={ReleaseTask: "task_id"})
def publish_task(task_id=None):
    """
    Publish a task by sending it the publish command.
    """
    task = ReleaseTask.objects.get(pk=task_id)
    try:
        task.publish()
        task.save()
    except Exception as err:
        logger.error(f"There was a problem trying to publish the task: {err}")
        logger.warning(
            "The release will be canceled as the service failed to publish "
            "the task. Be cautious of undesired end states as some other "
            "tasks may have published their data!"
        )
        task.failed()
        task.save()

        task.release.cancel()
        task.release.save()

        queue = django_rq.get_queue("releases")
        queue.enqueue(
            cancel_release,
            release_id=task.release.pk,
            failed=True,
            ttl=settings.RQ_DEFAULT_TTL,
        )


@task("release", related_models={Release: "release_id"})
def cancel_release(release_id=None, failed=False):
    """
    Cancel a release by sending the cancel action to each service in the
    release.
    """
    logger.info(f"Canceling release {release_id}")

    release = Release.objects.select_related().get(kf_id=release_id)
    tasks = release.tasks.exclude(state="failed").all()

    target = "failed" if failed else "canceled"
    # If there are no tasks in our release, just push it to the canceled or
    # failed state automatically.
    if not tasks:
        logger.info(
            f"No services were requested to run for release '{release.pk}'. "
            f"The release will be automatically moved to the '{target}' state."
        )
        if failed:
            release.failed()
        else:
            release.canceled()
        release.save()
        return

    # Iterate through each task sequentially and tell it to cancel
    for task in tasks:
        logger.info(
            f"Queuing cancel_task for task '{task.pk}' "
            f"of service '{task.release_service.name}'"
        )
        queue = django_rq.get_queue("releases")
        queue.enqueue(
            cancel_task, task_id=task.pk, ttl=settings.RQ_DEFAULT_TTL
        )


@task("release_task", related_models={ReleaseTask: "task_id"})
def cancel_task(task_id=None):
    """
    Cancel a task by sending it the cancel command.
    """
    task = ReleaseTask.objects.get(pk=task_id)

    try:
        task.cancel()
        task.save()
    except Exception as err:
        logger.error(f"There was a problem trying to cancel the task: {err}")
        logger.warning("Will mark the task as failed.")
        task.failed()
        task.save()


@task("scan_tasks")
def scan_tasks():
    """
    Queue tasks to update all active task's state
    """
    tasks = (
        ReleaseTask.objects.exclude(state="canceled")
        & ReleaseTask.objects.exclude(state="staged")
        & ReleaseTask.objects.exclude(state="rejected")
        & ReleaseTask.objects.exclude(state="failed")
        & ReleaseTask.objects.exclude(state="published")
    ).all()

    for task in tasks:
        logger.info(
            f"Queuing check_task for task '{task.pk}' in state '{task.state}'"
        )
        queue = django_rq.get_queue("releases")
        queue.enqueue(check_task, task_id=task.pk, ttl=settings.RQ_DEFAULT_TTL)


@task("release_task", related_models={ReleaseTask: "task_id"})
def check_task(task_id=None):
    """
    Check the task and update its state if needed
    """
    task = ReleaseTask.objects.get(pk=task_id)
    try:
        task.check_state()
    except Exception as err:
        logger.error(
            f"There was a problem checking the task's status: {err}. "
        )
        logger.warning("Will mark the task as failed.")
        task.failed()
        task.save()


@task("scan_releases")
def scan_releases():
    """
    Queue tasks to check any release in an active state.
    """
    releases = (
        Release.objects.filter(state="waiting")
        | Release.objects.filter(state="initializing")
        | Release.objects.filter(state="running")
        | Release.objects.filter(state="publishing")
        | Release.objects.filter(state="canceling")
    ).all()

    logger.info(f"Found {len(releases)} in states requiring action")
    for release in releases:

        logger.info(
            f"Queuing check_release for release '{release.pk}' in state "
            f"'{release.state}'"
        )
        queue = django_rq.get_queue("releases")
        queue.enqueue(
            check_release, release_id=release.pk, ttl=settings.RQ_DEFAULT_TTL
        )


@task("release", related_models={Release: "release_id"})
def check_release(release_id=None):
    """
    Check a release's state and schedule any jobs needed to move it foreward.
    """
    release = Release.objects.get(pk=release_id)
    logger.info(f"Checking if release '{release.pk} needs to update its state")
    logger.info(f"Current state of release '{release.pk}': {release.state}")
    states = {t.pk: t.state for t in release.tasks.all()}
    logger.info(f"Current state of tasks: {states}")

    # If all tasks are in canceled state, the release should assume the
    # canceled state.
    if release.state == "canceling" and all(
        [t.state == "canceled" for t in release.tasks.all()]
    ):
        release.canceled()
        release.save()
    # If all tasks are in either canceled or failed state, the release
    # will be marked as failed as at least one task must be marked as failed
    # due to us handling the all canceled condition above
    elif release.state == "canceling" and all(
        [
            t.state in ["rejected", "canceled", "failed"]
            for t in release.tasks.all()
        ]
    ):
        logger.info(
            "All tasks were found to be in terminal states. Failing release"
        )
        release.failed()
        release.save()

    # Check to see if we can start the releases
    elif release.state == "initializing" and all(
        [t.state == "pending" for t in release.tasks.all()]
    ):
        logger.info("All tasks are pending. Starting release")
        release.start()
        release.save()
        queue = django_rq.get_queue("releases")
        queue.enqueue(
            start_release, release_id=release.pk, ttl=settings.RQ_DEFAULT_TTL
        )

    # Check to see if we can mark the release as staged
    elif release.state == "running" and all(
        [t.state == "staged" for t in release.tasks.all()]
    ):
        logger.info("All tasks are staged. Setting release to 'staged'")
        release.staged()
        release.save()
    # Check to see if we can mark the release as published
    elif release.state == "publishing" and all(
        [t.state == "published" for t in release.tasks.all()]
    ):
        release.complete()
        release.save()

    # Finally, we need to check if one of the tasks did end up in a cancel
    # or fail transition so we can start the fail or cancel process
    elif release.state not in ["canceling", "canceled", "failed"] and any(
        task.state
        in ["canceling", "failing", "failed", "canceled", "rejected"]
        for task in release.tasks.all()
    ):
        # Check if one of the tasks failed so we can mark the release as a
        # failure
        failed = False
        if any(task.state == "failed" for task in release.tasks.all()):
            logger.info("A task failed. Failing the release")
            failed = True

        logger.info("A task stopped unexpectedly. Canceling the release")
        release.cancel()
        release.save()

        queue = django_rq.get_queue("releases")
        queue.enqueue(
            cancel_release,
            release_id=release.pk,
            failed=failed,
            ttl=settings.RQ_DEFAULT_TTL,
        )
