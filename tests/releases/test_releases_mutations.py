import pytest
from graphql_relay import to_global_id

from creator.releases.models import Release
from creator.releases.factories import ReleaseFactory


CREATE_RELEASE = """
mutation ($input: CreateReleaseInput!) {
    createRelease(input: $input) {
        release {
            id
        }
    }
}
"""

UPDATE_RELEASE = """
mutation ($id: ID!, $input: UpdateReleaseInput!) {
    updateRelease(id: $id, input: $input) {
        release {
            id
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
def test_create_release(db, clients, user_group, allowed):
    """
    Test the create mutation.
    """
    client = clients.get(user_group)

    resp = client.post(
        "/graphql",
        data={
            "query": CREATE_RELEASE,
            "variables": {"input": {"name": "Test"}},
        },
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["createRelease"]["release"] is not None
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


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
                "id": to_global_id("ReleaseNode}}", release.pk),
                "input": {"name": "test"},
            },
        },
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["updateRelease"]["release"] is not None
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
