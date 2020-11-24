import pytest
from graphql_relay import to_global_id

from creator.releases.models import Release
from creator.releases.factories import ReleaseFactory

UPDATE_RELEASE = """
mutation ($id: ID!, $input: UpdateReleaseInput!) {
    updateRelease(id: $id, input: $input) {
        release {
            id
            name
            description
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
def test_update_release(db, clients, user_group, allowed):
    """
    Test the update mutation.
    """
    client = clients.get(user_group)

    release = ReleaseFactory()

    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_RELEASE,
            "variables": {
                "id": to_global_id("ReleaseNode", release.pk),
                "input": {"name": "test", "description": "Lorem Ipsum"},
            },
        },
        content_type="application/json",
    )

    if allowed:
        body = resp.json()
        assert body["data"]["updateRelease"]["release"] is not None
        assert (
            body["data"]["updateRelease"]["release"]["description"]
            == "Lorem Ipsum"
        )
        assert body["data"]["updateRelease"]["release"]["name"] == "test"
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_update_release_does_not_exist(db, clients):
    """
    Test the update mutation.
    """
    client = clients.get("Administrators")

    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_RELEASE,
            "variables": {
                "id": to_global_id("ReleaseNode", "ABC"),
                "input": {"name": "test", "description": "Lorem Ipsum"},
            },
        },
        content_type="application/json",
    )

    assert (
        resp.json()["errors"][0]["message"] == "Release ABC does not exist"
    )
