import pytest
from unittest.mock import call
from creator.files.models import File, FileType
from creator.ingest_runs.models import IngestRun
from creator.ingest_runs.tasks import (
    run_ingest,
    cancel_ingest,
)

from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def mock_enqueue(mocker):
    """
    Mock the django_eq.enqueue function.
    """
    enqueue = mocker.patch("creator.ingest_runs.tasks.django_rq.enqueue")
    return enqueue


def test_run_ingest(db, mocker, clients, prep_file):
    """
    Test the run_ingest function.
    """
    client = clients.get("Administrator")
    mock_genomic_workflow = mocker.patch(
        "creator.ingest_runs.tasks.ingest_genomic_workflow_output_manifests"
    )
    user = User.objects.first()

    # Create data. The last Version will have a non-GWO FileType
    for _ in range(3):
        prep_file(authed=True)
    files = list(File.objects.all())
    for file_ in files[:-1]:
        file_.file_type = FileType.GWO.value
        file_.save()
    file_versions = [f.versions.first() for f in files]

    """
    1) Happy Case
    Call run_ingest. Check that genomic_file_workflow got
    called. Check that ir.state == 'completed'.
    """
    happy_versions = file_versions[:-1]
    # An initial IngestRun with no issues
    happy_ir = setup_ingest_run(happy_versions, user)
    run_ingest(happy_ir.id)

    assert IngestRun.objects.all().count() == 1
    mock_genomic_workflow.assert_called_once()
    mock_genomic_workflow.reset_mock()
    happy_ir = IngestRun.objects.get(pk=happy_ir.id)
    assert happy_ir.state == "completed"

    """
    2) Non-GWO Case
    Call run_ingest on an IngestRun with a version that doesn't have a GWO
    root_file. Exception should be raised, and state should become failed.
    """
    bad_ir = setup_ingest_run(file_versions, user)
    with pytest.raises(Exception):
        assert run_ingest(bad_ir.id)
    bad_ir = IngestRun.objects.get(pk=bad_ir.id)
    assert bad_ir.state == "failed"

    """
    3) Exception Case
    Call run_ingest on an IngestRun with all GWO versions. Mock out
    _ingest_genomic_workflow_manifest_ and give it an exception side effect
    and check that the IngestRun goes to a failed state.
    """
    except_ir = setup_ingest_run(happy_versions[:1], user)
    mock_genomic_workflow.side_effect = Exception
    with pytest.raises(Exception):
        run_ingest(except_ir.id)
    mock_genomic_workflow.assert_called_once()
    except_ir = IngestRun.objects.get(pk=except_ir.id)
    assert except_ir.state == "failed"


def setup_ingest_run(file_versions, user):
    ir = IngestRun()
    ir.creator = user
    ir.save()
    ir.versions.set(file_versions)
    ir.save()
    return ir
