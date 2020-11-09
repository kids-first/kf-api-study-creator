import pytest
from graphql_relay import to_global_id
from creator.files.models import File


START_INGEST_RUN = """
mutation ($input: StartIngestRunInput!) {
    startIngestRun(input: $input) {
        ingestRun {
            id
            name
            inputHash
            versions { edges { node { id kfId } } }
        }
    }
}
"""

CANCEL_INGEST_RUN = """
mutation ($id: ID!) {
    cancelIngestRun(id: $id) {
        ingestRun {
            id
            name
            inputHash
            versions { edges { node { id kfId } } }
        }
    }
}
"""


@pytest.fixture
def mock_ingest_job(mocker):
    """
    Mock ingest job
    """
    ingest_job = mocker.patch("creator.studies.schema.django_rq.enqueue")
    return ingest_job


def send_query(client, query, input_dict):
    return client.post(
        "/graphql",
        data={
            "query": query,
            "variables": {"input": input_dict},
        },
        content_type="application/json",
    )


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
def test_start_ingest_run(
    db, clients, prep_file, mock_ingest_job, user_group, allowed
):
    """
    Test the start ingest run mutation
    """
    client = clients.get(user_group)

    # Create a study with some files
    for i in range(2):
        prep_file(authed=True)
    version_ids = [
        to_global_id("VersionNode", f.versions.first().kf_id)
        for f in File.objects.all()
    ]

    # Start a valid ingest runs for a batch of file versions
    resp = send_query(client, START_INGEST_RUN, {"versions": version_ids})

    if allowed:
        ir = resp.json()["data"]["startIngestRun"]["ingestRun"]
        assert ir["name"]
        assert ir["inputHash"]
        for version in ir["versions"]["edges"]:
            version["node"]["kfId"] in ir["name"]

    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "user_group",
    [
        ("Administrators"),
    ],
)
def test_start_ingest_run_invalid(db, clients, prep_file, user_group):
    """
    Ingest run with no attached versions should raise ValidationError
    """
    client = clients.get(user_group)
    resp = send_query(client, START_INGEST_RUN, {"versions": []})
    assert "at least 1 file Version" in resp.json()["errors"][0]["message"]


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
def test_cancel_ingest_run(
    db, clients, ingest_runs, mock_ingest_job, user_group, allowed
):
    """
    Test the cancel ingest run mutation.
    """
    client = clients.get(user_group)

    ingest_run = ingest_runs(n=1)[0]

    resp = client.post(
        "/graphql",
        data={
            "query": CANCEL_INGEST_RUN,
            "variables": {
                "id": to_global_id("IngestRunNode", ingest_run.id),
            },
        },
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["cancelIngestRun"]["ingestRun"] is not None
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
