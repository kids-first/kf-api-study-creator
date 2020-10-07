import pytest
from graphql_relay import to_global_id
from creator.releases.factories import ReleaseTaskFactory

RELEASE_TASK = """
query ($id: ID!) {
    releaseTask(id: $id) {
        id
    }
}
"""

ALL_RELEASE_TASKS = """
query {
    allReleaseTasks {
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
def test_query_release_task(db, clients, user_group, allowed):
    client = clients.get(user_group)

    release_task = ReleaseTaskFactory()

    variables = {"id": to_global_id("ReleaseTaskNode", release_task.kf_id)}

    resp = client.post(
        "/graphql",
        data={"query": RELEASE_TASK, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["releaseTask"]["id"] == to_global_id(
            "ReleaseTaskNode", release_task.kf_id
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
def test_query_all_release_tasks(db, clients, user_group, allowed):
    client = clients.get(user_group)

    release_tasks = ReleaseTaskFactory.create_batch(5)

    resp = client.post(
        "/graphql",
        data={"query": ALL_RELEASE_TASKS},
        content_type="application/json",
    )

    if allowed:
        assert len(resp.json()["data"]["allReleaseTasks"]["edges"]) == 5
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
