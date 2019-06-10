import pytest
from creator.events.models import Event


ALL_EVENTS = """
query (
    $studyId: String,
    $fileId: String,
    $versionId: String,
    $createdAt_Gt: DateTime,
    $createdAt_Lt: DateTime,
    $user_Username: String,
    $eventType: String,
) {
    allEvents(
        study_KfId: $studyId,
        file_KfId: $fileId,
        version_KfId: $versionId,
        createdAt_Gt: $createdAt_Gt,
        createdAt_Lt: $createdAt_Lt,
        user_Username: $user_Username,
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
    "user_type,authorized,expected",
    [
        ("admin", True, 2),
        ("admin", False, 2),
        ("service", True, 2),
        ("service", False, 2),
        ("user", True, 2),
        ("user", False, 0),
        (None, True, 0),
        (None, False, 0),
    ],
)
def test_event_query_roles(
    db,
    admin_client,
    service_client,
    user_client,
    client,
    prep_file,
    user_type,
    authorized,
    expected,
):
    """
    Test that each role resolves the correct events
    ADMIN - can query all events
    SERVICE - can query all events
    USER - can query events for studies that are in their groups
    unauthed - can not query events
    """
    study_id, file_id, version_id = prep_file(authed=authorized)

    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    resp = api_client.post(
        "/graphql", content_type="application/json", data={"query": ALL_EVENTS}
    )
    # Test that the correct number of events are returned
    assert len(resp.json()["data"]["allEvents"]["edges"]) == expected
