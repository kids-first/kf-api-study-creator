import pytest
from graphql_relay import to_global_id

from creator.files.models import File
from creator.ingest_runs.models import IngestRun
from creator.ingest_runs.mutations import cancel_duplicate_ingest_runs


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


@pytest.fixture
def mock_ingest_queue(mocker):
    """
    Mock the IngestRun queue.
    """
    ingest_queue = mocker.patch(
        "creator.ingest_runs.mutations.IngestRun.queue",
        new_callable=mocker.PropertyMock,
    )
    return ingest_queue


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
    db,
    mocker,
    clients,
    prep_file,
    mock_ingest_job,
    mock_ingest_queue,
    user_group,
    allowed,
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

    # Start valid ingest runs for a batch of file versions
    resp = send_query(client, START_INGEST_RUN, {"versions": version_ids})

    if allowed:
        ir = resp.json()["data"]["startIngestRun"]["ingestRun"]
        assert ir["name"]
        assert ir["inputHash"]
        for version in ir["versions"]["edges"]:
            assert version["node"]["kfId"] in ir["name"]

        # Check that the call to ingest_run.queue.enqueue occurs
        mock_ingest_queue.assert_called_once()
        mock_ingest_queue.reset_mock()

    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "user_group",
    [
        ("Administrators"),
    ],
)
def test_start_duplicate_run(
    db, mocker, clients, prep_file, mock_ingest_job, user_group
):
    """
    Test the initialization of a start IngestRun mutation for a duplicate
    IngestRun.
    """
    mock_cancel_duplicate = mocker.patch(
        "creator.ingest_runs.mutations.cancel_duplicate_ingest_runs"
    )
    client = clients.get(user_group)
    # Create a study with some files
    for _ in range(2):
        prep_file(authed=True)
    version_ids = [
        to_global_id("VersionNode", f.versions.first().kf_id)
        for f in File.objects.all()
    ]

    # Start valid ingest runs for a batch of file versions
    resp = send_query(client, START_INGEST_RUN, {"versions": version_ids})

    # Start another valid ingest run for the same versions. This should cause
    # the previous IngestRun to get canceled.
    resp2 = send_query(client, START_INGEST_RUN, {"versions": version_ids})
    # Check that the correct enqueue call occurred.
    mock_cancel_duplicate.assert_called_once()


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


def test_start_ingest_run_bad_version(db, clients, prep_file):
    """
    Starting an ingest run with an invalid Version ID should
    raise GraphQLError.
    """
    client = clients.get("Administrators")
    prep_file(authed=True)
    fake_id = File.objects.first().versions.first().kf_id
    fake_global = to_global_id("VersionNode", fake_id)
    # Now delete the version
    File.objects.first().delete()
    resp = send_query(client, START_INGEST_RUN, {"versions": [fake_global]})
    assert f"The Version {fake_id}" in resp.json()["errors"][0]["message"]


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
    db, mocker, clients, ingest_runs, mock_ingest_job, user_group, allowed
):
    """
    Test the cancel ingest run mutation.
    """
    mock_ingest_queue = mocker.patch(
        "creator.ingest_runs.mutations.IngestRun.queue",
        new_callable=mocker.PropertyMock,
    )
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
        mock_ingest_queue.assert_called_once()
        mock_ingest_queue.reset_mock()
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_cancel_ingest_run_bad_version(db, clients):
    """
    Canceling an IngestRun with an invalid ID should raise GraphQLError.
    """
    client = clients.get("Administrators")
    ir = IngestRun()
    ir.save()
    fake_id = IngestRun.objects.first().id
    # now delete the ingestrun
    IngestRun.objects.first().delete()
    resp = client.post(
        "/graphql",
        data={
            "query": CANCEL_INGEST_RUN,
            "variables": {
                "id": to_global_id("ingestrunnode", fake_id),
            },
        },
        content_type="application/json",
    )
    assert f"IngestRun {fake_id} was" in resp.json()["errors"][0]["message"]


def test_cancel_duplicate_ingest_runs(
    db, mocker, clients, prep_file, mock_ingest_queue
):
    """
    Test the cancel_duplicate_ingest_runs helper function.
    """
    client = clients.get("Administrators")
    # create two ingest runs with the same input hash
    for i in range(2):
        prep_file(authed=True)
    file_versions = [f.versions.first() for f in File.objects.all()]

    ir1 = IngestRun()
    ir1.save()
    ir1.versions.set(file_versions)
    ir1.save()
    ir2 = IngestRun()
    ir2.save()
    ir2.versions.set(file_versions)
    ir2.save()
    irs = (ir1, ir2)
    assert IngestRun.objects.all().count() == 2
    cancel_duplicate_ingest_runs(irs)
    assert mock_ingest_queue.call_count == 2
