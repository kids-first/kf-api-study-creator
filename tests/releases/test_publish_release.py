import pytest
from graphql_relay import to_global_id

from creator.releases.tasks import publish_release, publish_task
from creator.releases.models import Release
from creator.releases.factories import (
    ReleaseFactory,
    ReleaseTaskFactory,
    ReleaseServiceFactory,
)


PUBLISH_RELEASE = """
mutation ($release: ID!) {
    publishRelease(release: $release) {
        release {
            id
            state
        }
    }
}
"""


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", False),
        ("Investigators", False),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_publish_release(db, clients, user_group, allowed):
    """
    Test the publish mutation.
    """
    client = clients.get(user_group)

    release = ReleaseFactory(state="staged")

    resp = client.post(
        "/graphql",
        data={
            "query": PUBLISH_RELEASE,
            "variables": {"release": to_global_id("ReleaseNode", release.pk)},
        },
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["publishRelease"]["release"] is not None
        assert (
            resp.json()["data"]["publishRelease"]["release"]["state"]
            == "publishing"
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "state,allowed",
    [
        ("waiting", False),
        ("initializing", False),
        ("running", False),
        ("staged", True),
        ("publishing", False),
        ("published", False),
        ("failed", False),
        ("published", False),
    ],
)
def test_publish_allowed_states(db, clients, mocker, state, allowed):
    """
    Test that publishing may only occur from valid states
    """
    mock = mocker.patch("creator.releases.models.ReleaseTask.publish")
    client = clients.get("Administrators")

    release = ReleaseFactory(state=state)
    release.tasks.set(ReleaseTaskFactory.create_batch(3, state="staged"))
    release.save()

    resp = client.post(
        "/graphql",
        data={
            "query": PUBLISH_RELEASE,
            "variables": {"release": to_global_id("ReleaseNode", release.pk)},
        },
        content_type="application/json",
    )

    release.refresh_from_db()

    if allowed:
        assert resp.json()["data"]["publishRelease"]["release"] is not None
        assert (
            resp.json()["data"]["publishRelease"]["release"]["state"]
            == "publishing"
        )
        assert release.state == "publishing"
    else:
        assert f"Can't switch from state '{state}'" in (
            resp.json()["errors"][0]["message"]
        )


def test_start_release_unknown_release(db, clients):
    """
    Test that publishing of an unknown release cannot occur
    """
    client = clients.get("Administrators")

    variables = {"release": to_global_id("ReleaseNode", "RE_00000000")}

    resp = client.post(
        "/graphql",
        data={"query": PUBLISH_RELEASE, "variables": variables},
        content_type="application/json",
    )

    assert (
        resp.json()["errors"][0]["message"]
        == "Release RE_00000000 does not exist"
    )


def test_publish_release_no_tasks(db):
    """
    Test that a release is immediately published if it has no tasks.
    """
    release = ReleaseFactory(state="publishing")
    release.tasks.set([])
    release.save()

    publish_release(release_id=release.pk)

    release.refresh_from_db()
    assert release.state == "published"


def test_publish_release_with_tasks(db, mocker):
    """
    Test that a release sends commands to all tasks to publish
    """

    mock = mocker.patch("rq.Queue.enqueue")

    release = ReleaseFactory(state="publishing")
    tasks = ReleaseTaskFactory.create_batch(3, state="staged")
    release.tasks.set(tasks)
    release.save()

    publish_release(release_id=release.pk)

    assert mock.call_count == 3
    assert release.state == "publishing"


def test_publish_task_successful(db, mocker):
    """
    Test that the publish_task task properly moves the task's state foreward
    """
    release = ReleaseFactory(state="publishing")
    service = ReleaseServiceFactory()
    task = ReleaseTaskFactory(
        state="staged", release=release, release_service=service
    )

    mock = mocker.patch("creator.releases.models.ReleaseTask._send_action")
    mock.return_value = {
        "state": "publishing",
        "task_id": task.pk,
        "release_id": release.pk,
    }

    publish_task(task.pk)

    task.refresh_from_db()

    assert task.state == "publishing"
    assert mock.call_count == 1


def test_publish_task_fail(db, mocker):
    """
    Test that tasks that respond with anything other than 'publishing' cancel
    the release.
    """
    release = ReleaseFactory(state="publishing")
    service = ReleaseServiceFactory()
    task = ReleaseTaskFactory(
        state="staged", release=release, release_service=service
    )

    mock = mocker.patch("creator.releases.models.ReleaseTask._send_action")
    mock.return_value = {
        "state": "invalid state",
        "task_id": task.pk,
        "release_id": release.pk,
    }

    publish_task(task.pk)

    task.refresh_from_db()

    assert task.state == "failed"
    assert mock.call_count == 1
    mock.assert_called_with("publish")
