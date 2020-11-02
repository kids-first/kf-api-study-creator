import pytest
from graphql_relay import to_global_id
from creator.releases.factories import ReleaseEventFactory

RELEASE_EVENT = """
query ($id: ID!) {
    releaseEvent(id: $id) {
        id
    }
}
"""

ALL_RELEASE_EVENTS = """
query {
    allReleaseEvents {
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
def test_query_release_event(db, clients, user_group, allowed):
    client = clients.get(user_group)

    release_event = ReleaseEventFactory()

    variables = {"id": to_global_id("ReleaseEventNode", release_event.pk)}

    resp = client.post(
        "/graphql",
        data={"query": RELEASE_EVENT, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["releaseEvent"]["id"] == to_global_id(
            "ReleaseEventNode", release_event.pk
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
def test_query_all_release_events(db, clients, user_group, allowed):
    client = clients.get(user_group)

    release = ReleaseEventFactory.create_batch(5)

    resp = client.post(
        "/graphql",
        data={"query": ALL_RELEASE_EVENTS},
        content_type="application/json",
    )

    if allowed:
        assert len(resp.json()["data"]["allReleaseEvents"]["edges"]) == 5
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
