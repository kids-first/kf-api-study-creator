import pytest
from django.contrib.auth import get_user_model

from creator.models import Job
from creator.tasks import sync_buckets_task


def test_sync_buckets_success(db, mocker):
    """
    Test that the sync task operates correctly when the setup succeeds
    """
    job = Job(name="buckets_sync")
    job.save()
    mock = mocker.patch("creator.tasks.sync_buckets")

    assert job.last_run is None

    sync_buckets_task()

    job.refresh_from_db()
    assert job.last_run is not None
    assert job.failing is False
    assert job.last_error == ""
    assert mock.call_count == 1


def test_sync_buckets_error(db, mocker):
    job = Job(name="buckets_sync")
    job.save()

    mock = mocker.patch("creator.tasks.sync_buckets")
    mock.side_effect = Exception("error")

    with pytest.raises(Exception):
        sync_buckets_task()

    job.refresh_from_db()
    assert job.failing
    assert job.last_error == "error"
