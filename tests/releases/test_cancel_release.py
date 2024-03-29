import pytest
from graphql_relay import to_global_id

from creator.releases.models import Release
from creator.releases.factories import ReleaseFactory


CANCEL_RELEASE = """
mutation ($release: ID!) {
    cancelRelease(release: $release) {
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
def test_cancel_release(db, clients, user_group, allowed):
    """
    Test the cancel mutation.
    """
    client = clients.get(user_group)

    release = ReleaseFactory(state="running")

    resp = client.post(
        "/graphql",
        data={
            "query": CANCEL_RELEASE,
            "variables": {"release": to_global_id("ReleaseNode", release.pk)},
        },
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["cancelRelease"]["release"] is not None
        assert (
            resp.json()["data"]["cancelRelease"]["release"]["state"]
            == "canceling"
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "state,allowed",
    [
        ("waiting", True),
        ("initializing", True),
        ("running", True),
        ("staged", True),
        ("publishing", True),
        ("published", False),
        ("failed", False),
        ("canceled", False),
    ],
)
def test_cancel_allowed_states(db, clients, state, allowed):
    """
    Test that canceling may only occur from valid states with appropriate
    end dates
    """
    client = clients.get("Administrators")

    release = ReleaseFactory(state=state)
    assert release.ended_at is None if allowed else not None

    resp = client.post(
        "/graphql",
        data={
            "query": CANCEL_RELEASE,
            "variables": {"release": to_global_id("ReleaseNode", release.pk)},
        },
        content_type="application/json",
    )

    release.refresh_from_db()

    if allowed:
        assert resp.json()["data"]["cancelRelease"]["release"] is not None
        assert (
            resp.json()["data"]["cancelRelease"]["release"]["state"]
            == "canceling"
        )
        assert release.state == "canceled"
        assert release.ended_at is not None
    else:
        assert f"Can't switch from state '{state}'" in (
            resp.json()["errors"][0]["message"]
        )


def test_cancel_release_does_not_exist(db, clients):
    """
    Test that a release that does not exist cannot be canceled
    """
    client = clients.get("Administrators")

    release = ReleaseFactory(state="running")

    resp = client.post(
        "/graphql",
        data={
            "query": CANCEL_RELEASE,
            "variables": {"release": to_global_id("ReleaseNode", "ABC")},
        },
        content_type="application/json",
    )

    assert resp.json()["errors"][0]["message"] == "Release ABC does not exist"
