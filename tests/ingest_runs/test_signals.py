from creator.data_reviews.factories import DataReviewFactory
from creator.files.models import File, Version
from creator.ingest_runs.models import IngestRun, State
from creator.ingest_runs.factories import ValidationRunFactory
from creator.ingest_runs.signals import (
    cancel_invalid_ingest_runs,
    cancel_invalid_validation_runs,
)
from creator.ingest_runs.tasks import cancel_ingest, cancel_validation

from django.contrib.auth import get_user_model
from itertools import chain, combinations
from unittest.mock import call

User = get_user_model()


def test_data_review_delete(db, mocker, clients, data_review):
    """
    Test all validation runs for a data review to be deleted, are cancelled
    before the review's deletion
    """
    mock_enqueue = mocker.patch(
        "creator.ingest_runs.signals.django_rq.enqueue"
    )
    # Create some data - a data review with two validation runs, one active and
    # one failed
    user = User.objects.first()
    vrs = [
        ValidationRunFactory(data_review=data_review, state=x, creator=user)
        for x in (State.RUNNING, State.FAILED)
    ]

    # Delete the data review
    # Should result in cancellation of the running validation
    data_review.delete()
    expected_args = [
        call(cancel_validation, str(run.id)) for run in vrs[0:1]
    ]
    mock_enqueue.assert_has_calls(expected_args, any_order=True)


def test_cancel_invalid_validation_runs(db, mocker, clients, prep_file):
    """
    Test the cancel_invalid_validation_runs function.
    """
    mock_enqueue = mocker.patch(
        "creator.ingest_runs.signals.django_rq.enqueue"
    )
    # Create some data - 3 reviews with one running validation run
    # First two reviews share same version, third review has different version
    user = User.objects.first()
    versions = []
    for i in range(2):
        _, _, version_id = prep_file(authed=True)
        versions.append(Version.objects.get(pk=version_id))
    vrs = []
    drs = []
    for i in range(3):
        vers = versions[1:] if i == 2 else versions[:1]
        dr = DataReviewFactory(versions=vers)
        vr = ValidationRunFactory(
            state=State.RUNNING, data_review=dr, creator=user
        )
        drs.append(dr)
        vrs.append(vr)

    # Cancel the validation runs involving version 0
    # Should result in canceling validation runs 0, 1
    cancel_invalid_validation_runs(versions[0])
    expected_args = [
        call(cancel_validation, str(run.id)) for run in vrs[0:2]
    ]
    mock_enqueue.assert_has_calls(expected_args, any_order=True)


def test_cancel_invalid_ingest_runs(db, mocker, clients, prep_file):
    """
    Test the cancel_invalid_ingest_runs function.
    """
    client = clients.get("Administrator")
    mock_enqueue = mocker.patch(
        "creator.ingest_runs.signals.django_rq.enqueue"
    )
    user = User.objects.first()

    for _ in range(4):
        prep_file(authed=True)
    v1, v2, v3, v4 = [f.versions.first() for f in File.objects.all()]

    # Start IngestRuns for each combination of v1, v2, and v3
    powerset = list(
        chain.from_iterable(
            combinations((v1, v2, v3), size) for size in range(1, 4)
        )
    )
    """
    This gives us the following IRs:
    (1), (2), (3), (1, 2), (2, 3), (1, 3), (1, 2, 3)
    """
    ingests_with_v1 = []
    for versions in powerset:
        ingest = setup_ir(versions, user)
        if v1 in versions:
            ingests_with_v1.append(ingest.id)

    assert IngestRun.objects.all().count() == len(powerset)

    # Case 1: Normal. Cancel IngestRuns associated with Version v1.
    # I.E. (1), (1, 2), (1, 3), (1, 2, 3)
    cancel_invalid_ingest_runs(v1)
    assert mock_enqueue.call_count == len(ingests_with_v1)
    expected_args = [call(cancel_ingest, ir_id) for ir_id in ingests_with_v1]
    mock_enqueue.assert_has_calls(expected_args, any_order=True)
    mock_enqueue.reset_mock()

    # Case 2: Cancel IngestRuns for a Version with none associated
    cancel_invalid_ingest_runs(v4)
    assert mock_enqueue.call_count == 0


def test_file_version_pre_delete(db, mocker, clients, prep_file):
    """
    Test that the pre_delete signals are properly called and
    function accordingly.
    """
    mock_cancel_ingest = mocker.patch(
        "creator.ingest_runs.signals.cancel_invalid_ingest_runs"
    )
    mock_cancel_validation = mocker.patch(
        "creator.ingest_runs.signals.cancel_invalid_validation_runs"
    )
    mocks = [mock_cancel_ingest, mock_cancel_validation]

    # Create data
    for _ in range(4):
        prep_file(authed=False)
    files = list(File.objects.all())
    f1 = files[0]
    v1, v2, v3, v4 = [f.versions.first() for f in files]
    # Make sure two of the Versions have the same root file
    v2.root_file = f1
    v2.save()

    # Case 1: A Version is deleted.
    v4.delete()
    for mock_cancel in mocks:
        mock_cancel.assert_called_once_with(v4)
        mock_cancel.reset_mock()

    # Case 2: A File is deleted. Since this is done with cascade in the
    # database, not sure how to check for the correct arguments (or if this is
    # actually necessary).
    f1.delete()
    for mock_cancel in mocks:
        assert mock_cancel.call_count == 2


def setup_ir(file_versions, user):
    ir = IngestRun()
    ir.creator = user
    ir.save()
    ir.versions.set(file_versions)
    ir.save()
    ir.start()
    ir.save()
    return ir
