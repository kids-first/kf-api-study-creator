import logging
import requests
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
