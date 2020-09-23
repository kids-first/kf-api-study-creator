import pytest
from django.contrib.auth import get_user_model

from creator.models import Job
from creator.events.models import Event
from creator.tasks import sync_dataservice_studies_task


def test_dataservice_study_sync_task(db, mocker):
    """
    Test that the dataservice sync task is run correctly
    """
    job = Job(name="dataservice_sync")
    job.save()

    mock = mocker.patch("creator.tasks.sync_dataservice_studies")

    sync_dataservice_studies_task()

    job.refresh_from_db()
    assert job.last_run is not None
    assert job.failing is False
    assert job.last_error == ""
    assert mock.call_count == 1


def test_dataservice_study_sync_task_error(db, mocker):
    """
    test that errors are logged correctly
    """
    job = Job(name="dataservice_sync")
    job.save()

    mock = mocker.patch("creator.tasks.sync_dataservice_studies")
    mock.side_effect = Exception("error occurred")

    with pytest.raises(Exception):
        sync_dataservice_studies_task()

    job.refresh_from_db()
    assert mock.call_count == 1
    assert job.failing
    assert job.last_error == "error occurred"


def test_dataservice_study_sync_task_not_active(db, mocker):
    """
    Test that the job does not run if it's not active
    """
    job = Job(name="dataservice_sync", active=False)
    job.save()

    mock = mocker.patch("creator.tasks.sync_dataservice_studies")

    sync_dataservice_studies_task()

    assert mock.call_count == 0
