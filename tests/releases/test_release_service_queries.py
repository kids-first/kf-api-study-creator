import pytest
from graphql_relay import to_global_id
from creator.releases.factories import ReleaseServiceFactory

RELEASE_SERVICE = """
query ($id: ID!) {
    releaseService(id: $id) {
        id
    }
}
"""

ALL_RELEASE_SERVICES = """
query {
    allReleaseServices {
        edges { node { id } }
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
def test_query_release_service(db, clients, user_group, allowed):
    client = clients.get(user_group)

    release_service = ReleaseServiceFactory()

    variables = {
        "id": to_global_id("ReleaseServiceNode", release_service.kf_id)
    }

    resp = client.post(
        "/graphql",
        data={"query": RELEASE_SERVICE, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["releaseService"]["id"] == to_global_id(
            "ReleaseServiceNode", release_service.kf_id
        )
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
def test_query_all_release_services(db, clients, user_group, allowed):
    client = clients.get(user_group)

    release = ReleaseServiceFactory.create_batch(5)

    resp = client.post(
        "/graphql",
        data={"query": ALL_RELEASE_SERVICES},
        content_type="application/json",
    )

    if allowed:
        assert len(resp.json()["data"]["allReleaseServices"]["edges"]) == 5
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
