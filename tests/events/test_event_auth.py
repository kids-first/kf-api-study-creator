import pytest
from creator.events.models import Event


ALL_EVENTS = """
query (
    $studyId: String,
    $fileId: String,
    $versionId: String,
    $createdAfter: DateTime,
    $createdBefore: DateTime,
    $username: String,
    $eventType: String,
) {
    allEvents(
        studyKfId: $studyId,
        fileKfId: $fileId,
        versionKfId: $versionId,
        createdAfter: $createdAfter,
        createdBefore: $createdBefore,
        username: $username,
        eventType: $eventType,
    ) {
        edges {
            node {
                id
                user {
                    username
                }
                file {
                    kfId
                }
                version {
                    kfId
                }
                study {
                    kfId
                }
            }
        }
    }
}
"""


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_event_query_roles(db, clients, versions, user_group, allowed):
    """
    Test that each role resolves the correct events
    """
    client = clients.get(user_group)
    study, file, version = versions

    resp = client.post(
        "/graphql", content_type="application/json", data={"query": ALL_EVENTS}
    )
    # Test that the correct number of events are returned
    if allowed:
        assert "data" in resp.json()
        assert "allEvents" in resp.json()["data"]
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
