import pytest
from graphql_relay import to_global_id

from creator.releases.tasks import publish
from creator.releases.models import Release
from creator.releases.factories import ReleaseFactory, ReleaseTaskFactory


PUBLISH_RELEASE = """
mutation ($id: ID!) {
    publishRelease(id: $id) {
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
            "variables": {"id": to_global_id("ReleaseNode", release.pk)},
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
    release.tasks.add(ReleaseTaskFactory(state="staged"))
    release.save()

    resp = client.post(
        "/graphql",
        data={
            "query": PUBLISH_RELEASE,
            "variables": {"id": to_global_id("ReleaseNode", release.pk)},
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


def test_publish_no_tasks(db):
    """
    Test that a release is immediately published if it has no tasks.
    """
    release = ReleaseFactory(state="publishing")
    release.tasks.set([])
    release.save()

    publish(release.pk)

    release.refresh_from_db()
    assert release.state == "published"


def test_publish_with_tasks(db, mocker):
    """
    Test that a release sends commands to all tasks to publish
    """

    mock = mocker.patch("creator.releases.models.ReleaseTask.publish")

    release = ReleaseFactory(state="publishing")
    tasks = ReleaseTaskFactory.create_batch(3, state="staged")
    release.tasks.set(tasks)
    release.save()

    publish(release.pk)

    assert mock.call_count == 3
    assert release.state == "publishing"
