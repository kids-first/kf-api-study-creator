import pytest
from graphql_relay import to_global_id

from creator.releases.models import Release
from creator.releases.factories import ReleaseFactory


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
def test_publish_allowed_states(db, clients, state, allowed):
    """
    Test that publishing may only occur from valid states
    """
    client = clients.get("Administrators")

    release = ReleaseFactory(state=state)

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
