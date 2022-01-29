import pytest
import pandas

from creator.files.models import AuditPrepState
from creator.files.factories import VersionFactory
from creator.studies.factories import StudyFactory
from creator.storage_analyses.tasks import expected_file as task
from creator.storage_analyses.factories import ExpectedFileFactory
from creator.storage_analyses.models import AuditState, ExpectedFile

from ..files.fixtures import make_file_upload_manifest


def test_bulk_update_audit_state(db):
    """
    Test helper _bulk_update_audit_state
    """
    files = ExpectedFileFactory.create_batch(
        5, audit_state=AuditState.NOT_SUBMITTED
    )
    task._bulk_update_audit_state(files, "start_submission")
    for f in files:
        assert f.audit_state == AuditState.SUBMITTING


def test_dataframe_to_expected_files(db, mocker):
    """
    Test helper _dataframe_to_expected_files
    """
    study = StudyFactory()
    mock_logger = mocker.patch(
        "creator.storage_analyses.tasks.expected_file.logger"
    )
    rows = [
        {
            "File Location": f"foo{i}.tsv",
            "Hash":  f"hash{i}",
            "Hash Algorithm": "MD5",
            "Size": i * 100,
            "Foo": "Bar"
        } for i in range(5)
    ]
    missing_req = {
        "Hash": "1234",
        "Hash Algorithm": "MD5"
    }
    df = pandas.DataFrame(rows + [rows[0].copy(), missing_req])
    files = task._dataframe_to_expected_files(df, study)

    assert len(files) == 5
    assert files[0]["study_id"] == study.pk
    assert files[0]["custom_fields"] == {"Foo": "Bar"}
    assert "file_location" in files[0]
    assert mock_logger.warning.call_count == 2


def test_prepare_audit_submission(db, mocker, make_file_upload_manifest):
    """
    Test task to prepare audit submission
    """
    mock_django_rq = mocker.patch(
        "creator.storage_analyses.tasks.expected_file.django_rq"
    )
    # Success
    version = make_file_upload_manifest(nrows=10)
    version.start_audit_prep()
    version.save()
    task.prepare_audit_submission(version.pk)
    version.refresh_from_db()
    assert mock_django_rq.enqueue.call_count == 1
    assert version.audit_prep_state == AuditPrepState.COMPLETED
    assert ExpectedFile.objects.count() == 10

    # Failure
    version = VersionFactory()
    version.start_audit_prep()
    version.save()
    with pytest.raises(Exception):
        task.prepare_audit_submission(version.pk)
    version.refresh_from_db()
    assert version.audit_prep_state == AuditPrepState.FAILED


def test_submit_expected_files(db, mocker):
    """
    Test submitting expected files to audit system
    """
    mock_dewrangle = mocker.patch(
        "creator.storage_analyses.tasks.expected_file.DewrangleClient"
    )
    mock_client = mock_dewrangle()
    study = StudyFactory()
    efs = ExpectedFileFactory.create_batch(
        10, audit_state=AuditState.NOT_SUBMITTED, study=study
    )

    # Success
    task.submit_expected_files_for_audit(efs)
    assert ExpectedFile.objects.filter(
        audit_state=AuditState.SUBMITTED
    ).count() == 10

    # Failure
    efs = ExpectedFileFactory.create_batch(
        5, audit_state=AuditState.NOT_SUBMITTED, study=study
    )
    mock_client.bulk_upsert_expected_files.side_effect = Exception
    with pytest.raises(Exception):
        task.submit_expected_files_for_audit(efs)
    assert ExpectedFile.objects.filter(
        audit_state=AuditState.FAILED
    ).count() == 5


def test_submit_study_for_audit(db, mocker):
    """
    Test task to submit study for audit
    """
    mock_logger = mocker.patch(
        "creator.storage_analyses.tasks.expected_file.logger"
    )
    mock_dewrangle = mocker.patch(
        "creator.storage_analyses.tasks.expected_file.DewrangleClient"
    )
    mock_submit = mocker.patch(
        "creator.storage_analyses.tasks.expected_file."
        "submit_expected_files_for_audit"
    )
    mock_client = mock_dewrangle()
    study = StudyFactory()
    efs = ExpectedFileFactory.create_batch(
        10, audit_state=AuditState.NOT_SUBMITTED, study=study
    )
    efs_in_progress = ExpectedFileFactory.create_batch(
        8, audit_state=AuditState.SUBMITTING, study=study
    )
    efs_failed = ExpectedFileFactory.create_batch(
        5, audit_state=AuditState.FAILED, study=study
    )

    task.submit_study_for_audit(study.pk)

    assert mock_client.upsert_organization.call_count == 1
    assert mock_client.upsert_study.call_count == 1
    assert mock_submit.call_count == 1

    expected_ids = [str(f.pk) for f in efs + efs_failed]
    args, _ = mock_submit.call_args_list[0]
    actual_ids = [str(f.pk) for f in args[0]]
    assert set(expected_ids) == set(actual_ids)


def test_submit_study_for_audit_errors(db, mocker):
    """
    Test task to submit study for audit error cases
    """
    mock_logger = mocker.patch(
        "creator.storage_analyses.tasks.expected_file.logger"
    )
    mock_dewrangle = mocker.patch(
        "creator.storage_analyses.tasks.expected_file.DewrangleClient"
    )
    mock_client = mock_dewrangle()
    study = StudyFactory()

    # No expected files to submit
    task.submit_study_for_audit(study.pk)
    assert mock_logger.info.call_count == 1
