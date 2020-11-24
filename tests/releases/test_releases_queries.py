import pytest
from graphql_relay import to_global_id
from creator.releases.models import Release
from creator.releases.factories import ReleaseFactory

RELEASE = """
query ($id: ID!) {
    release(id: $id) {
        id
    }
}
"""

ALL_RELEASES = """
query {
    allReleases {
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
def test_query_release(db, clients, user_group, allowed):
    client = clients.get(user_group)

    release = ReleaseFactory()

    variables = {"id": to_global_id("ReleaseNode", release.pk)}

    resp = client.post(
        "/graphql",
        data={"query": RELEASE, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["release"]["id"] == to_global_id(
            "ReleaseNode", release.pk
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
def test_query_all_releases(db, clients, user_group, allowed):
    client = clients.get(user_group)

    release = ReleaseFactory.create_batch(5)

    resp = client.post(
        "/graphql",
        data={"query": ALL_RELEASES},
        content_type="application/json",
    )

    if allowed:
        assert (
            len(resp.json()["data"]["allReleases"]["edges"])
            == Release.objects.count()
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
