import pytest
from graphql_relay import to_global_id

from creator.ingest_runs.models import IngestRun
from creator.ingest_runs.factories import IngestRunFactory


CREATE_INGEST_REQUEST = """
mutation ($input: CreateIngestRunInput!) {
    createIngestRun(input: $input) {
        ingestRun {
            id
        }
    }
}
"""

UPDATE_INGEST_REQUEST = """
mutation ($id: ID!, $input: UpdateIngestRunInput!) {
    updateIngestRun(id: $id, input: $input) {
        ingestRun {
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
def test_create_ingest_run(db, clients, user_group, allowed):
    """
    Test the create mutation.
    """
    client = clients.get(user_group)

    resp = client.post(
        "/graphql",
        data={
            "query": CREATE_INGEST_REQUEST,
            "variables": {"input": {"name": "Test"}}
        },
        content_type="application/json",
    )

    if allowed:
        assert (
            resp.json()["data"]["createIngestRun"][
                "ingestRun"]
            is not None
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
def test_update_ingest_run(db, clients, user_group, allowed):
    """
    Test the update mutation.
    """
    client = clients.get(user_group)

    ingest_run = IngestRunFactory()

    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_INGEST_REQUEST,
            "variables": {
                "id": to_global_id("IngestRunNode}}", ingest_run.id),
                "input": {"name": "test"},
            },
        },
        content_type="application/json",
    )

    if allowed:
        assert (
            resp.json()["data"]["updateIngestRun"][
                "ingestRun"]
            is not None
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
