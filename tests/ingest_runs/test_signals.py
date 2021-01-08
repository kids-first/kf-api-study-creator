from creator.files.models import File, Version
from creator.ingest_runs.models import IngestRun
from creator.ingest_runs.signals import cancel_invalid_ingest_runs
from creator.ingest_runs.tasks import cancel_ingest

from django.contrib.auth import get_user_model
from itertools import chain, combinations
from unittest.mock import call

User = get_user_model()


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
    mock_cancel = mocker.patch(
        "creator.ingest_runs.signals.cancel_invalid_ingest_runs"
    )
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
    mock_cancel.assert_called_once_with(v4)
    mock_cancel.reset_mock()

    # Case 2: A File is deleted. Since this is done with cascade in the
    # database, not sure how to check for the correct arguments (or if this is
    # actually necessary).
    f1.delete()
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
