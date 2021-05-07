import pytest
from graphql_relay import to_global_id, from_global_id
from django.contrib.auth import get_user_model
from creator.studies.models import Membership
from creator.data_reviews.factories import DataReviewFactory
from creator.ingest_runs.factories import ValidationRunFactory
from creator.ingest_runs.models import ValidationRun, State
from creator.ingest_runs.tasks import run_validation, cancel_validation

User = get_user_model()

START_VALIDATION_RUN = """
mutation ($input: StartValidationRunInput!) {
    startValidationRun(input: $input) {
        validationRun {
            id
            inputHash
            state
            dataReview { id kfId }
        }
    }
}
"""

CANCEL_VALIDATION_RUN = """
mutation ($id: ID!) {
    cancelValidationRun(id: $id) {
        validationRun {
            id
            inputHash
            state
            dataReview { id kfId }
        }
    }
}
"""


@pytest.fixture
def mock_valid_queue(mocker):
    """
    Mock the ValidationRun queue
    """
    ingest_queue = mocker.patch(
        "creator.ingest_runs.mutations.validation_run.ValidationRun.queue"
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
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_start_validation_run(
    db,
    clients,
    prep_file,
    mock_valid_queue,
    data_review,
    user_group,
    allowed,
):
    """
    Test the start validation run mutation
    """
    client = clients.get(user_group)
    if user_group:
        user = User.objects.filter(groups__name=user_group).first()
        Membership(collaborator=user, study=data_review.study).save()

    # Start valid validation runs for a batch of file versions
    dr_id = to_global_id("DataReviewNode", data_review.kf_id)
    resp = send_query(
        client, START_VALIDATION_RUN, {"dataReview": dr_id}
    )

    if allowed:
        vr = resp.json()["data"]["startValidationRun"]["validationRun"]
        assert vr["inputHash"]
        assert vr["state"] == State.INITIALIZING
        assert data_review.kf_id == vr["dataReview"]["kfId"]

        # Check that the run_validation task was queued
        mock_valid_queue.enqueue.call_count == 1
        args, _ = mock_valid_queue.enqueue.call_args_list[0]
        assert args[0] == run_validation
        mock_valid_queue.reset_mock()

    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "user_group",
    [
        ("Administrators"),
    ],
)
def test_start_duplicate_run(
    db, mocker, mock_valid_queue, clients, data_review, user_group
):
    """
    Test the initialization of a start ValidationRun mutation for a duplicate
    ValidationRun.
    """
    mock_cancel_duplicates = mocker.patch(
        "creator.ingest_runs.mutations.validation_run"
        ".cancel_duplicate_ingest_processes"
    )
    client = clients.get(user_group)
    dr_id = to_global_id("DataReviewNode", data_review.kf_id)

    # Start valid validation runs for a batch of file versions
    send_query(client, START_VALIDATION_RUN, {"dataReview": dr_id})

    # Start another valid validation run for the same versions.
    # This should cause the previous ValidationRun to get canceled.
    send_query(client, START_VALIDATION_RUN, {"dataReview": dr_id})

    # Check that cancel duplicates was called and run_validation was not called
    mock_valid_queue.enqueue.call_count == 0
    mock_cancel_duplicates.call_count == 1
    args, _ = mock_cancel_duplicates.call_args_list[0]
    assert set(args[1:]) == set([ValidationRun, cancel_validation])


@pytest.mark.parametrize(
    "user_group",
    [
        ("Administrators"),
    ],
)
def test_start_invalid_validation_run(db, clients, prep_file, user_group):
    """
    Validation run with no attached data_review or versions should raise
    ValidationError
    """
    client = clients.get(user_group)

    # Missing data review id
    resp = send_query(client, START_VALIDATION_RUN, {"dataReview": ""})
    assert "existing data review" in resp.json()["errors"][0]["message"]

    # Data review not found
    dr_id = to_global_id("DataReviewNode", "foo")
    resp = send_query(client, START_VALIDATION_RUN, {"dataReview": dr_id})
    assert "not found" in resp.json()["errors"][0]["message"]

    # Data review with no versions
    dr = DataReviewFactory()
    dr_id = to_global_id("DataReviewNode", dr.kf_id)
    resp = send_query(client, START_VALIDATION_RUN, {"dataReview": dr_id})
    assert "at least 1 file version" in resp.json()["errors"][0]["message"]


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
def test_cancel_validation_run(
    db, clients, mock_valid_queue, data_review, user_group, allowed
):
    """
    Test the cancel validation run mutation.
    """
    client = clients.get(user_group)
    if user_group:
        user = User.objects.filter(groups__name=user_group).first()
        Membership(collaborator=user, study=data_review.study).save()

    validation_run = ValidationRunFactory(data_review=data_review)
    resp = client.post(
        "/graphql",
        data={
            "query": CANCEL_VALIDATION_RUN,
            "variables": {
                "id": to_global_id(
                    "ValidationRunNode", validation_run.id
                ),
            },
        },
        content_type="application/json",
    )

    if allowed:
        vr = resp.json()["data"]["cancelValidationRun"]["validationRun"]
        assert vr is not None
        assert vr["state"] == State.CANCELING
        _, vr_id = from_global_id(vr["id"])
        mock_valid_queue.enqueue.assert_called_once_with(
            cancel_validation, args=(vr_id,)
        )
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_cancel_invalid_validation_run(db, clients):
    """
    Test canceling a validation run that doesn't exist
    """
    client = clients.get("Administrators")

    resp = client.post(
        "/graphql",
        data={
            "query": CANCEL_VALIDATION_RUN,
            "variables": {
                "id": to_global_id(
                    "ValidationRunNode", str(ValidationRun().pk)
                ),
            },
        },
        content_type="application/json",
    )
    assert "not found" in resp.json()["errors"][0]["message"]
