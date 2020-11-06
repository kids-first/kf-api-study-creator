import pytest
from graphql_relay import to_global_id
from creator.ingest_runs.factories import IngestRunFactory

INGEST_REQUEST = """
query ($id: ID!) {
    ingestRun(id: $id) {
        id
    }
}
"""

ALL_INGEST_REQUESTS = """
query {
    allIngestRuns {
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
def test_query_ingest_run(db, clients, user_group, allowed):
    client = clients.get(user_group)

    ingest_run = IngestRunFactory()

    variables = {"id": to_global_id("IngestRunNode", ingest_run.id)}

    resp = client.post(
        "/graphql",
        data={"query": INGEST_REQUEST, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert (
            resp.json()["data"]["ingestRun"]["id"] ==
            to_global_id("IngestRunNode", ingest_run.id)
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
def test_query_all_ingest_runs(db, clients, user_group, allowed):
    client = clients.get(user_group)

    ingest_run = IngestRunFactory.create_batch(5)

    resp = client.post(
        "/graphql",
        data={"query": ALL_INGEST_REQUESTS},
        content_type="application/json"
    )

    if allowed:
        assert len(resp.json()["data"]["allIngestRuns"]["edges"]) == 5
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
