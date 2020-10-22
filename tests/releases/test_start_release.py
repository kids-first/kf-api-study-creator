import pytest
from graphql_relay import to_global_id

from creator.releases.models import Release
from creator.releases.factories import ReleaseFactory


START_RELEASE = """
mutation ($input: StartReleaseInput!) {
    startRelease(input: $input) {
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
def test_start_release(db, clients, user_group, allowed):
    """
    Test the start release mutation.
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
        assert resp.json()["data"]["startRelease"]["release"] is not None
        assert (
            resp.json()["data"]["startRelease"]["release"]["state"]
            == "waiting"
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
