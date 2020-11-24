import pytest
from graphql_relay import to_global_id

from creator.studies.factories import StudyFactory
from creator.releases.factories import (
    ReleaseFactory,
    ReleaseTaskFactory,
    ReleaseServiceFactory,
)

from creator.releases.models import Release, ReleaseTask
from creator.releases.tasks import start_release, start_task


def test_start_release_no_tasks(db):
    """
    Test that the start_release task immediately goes to 'staged' when there
    are no services in the release
    """
    release = ReleaseFactory(state="running")

    start_release(release.pk)

    release.refresh_from_db()

    assert release.state == "staged"


def test_start_release_with_tasks(db, mocker):
    """
    Test that start_release queues start_task jobs for each task
    """
    mock_rq = mocker.patch("rq.Queue.enqueue")

    release = ReleaseFactory(state="running")
    service = ReleaseServiceFactory()
    task = ReleaseTaskFactory(
        release=release, release_service=service, state="initialized"
    )

    start_release(release.pk)

    release.refresh_from_db()

    assert release.state == "running"
    assert mock_rq.call_count == 1
    mock_rq.assert_called_with(start_task, task_id=task.pk, ttl=60)


def test_start_task_successful(db, mocker):
    """
    Test that the start_task task is successful when correct state is returned
    """
    release = ReleaseFactory(state="running")
    service = ReleaseServiceFactory()
    task = ReleaseTaskFactory(
        release=release, release_service=service, state="initialized"
    )

    mock = mocker.patch("creator.releases.models.ReleaseTask._send_action")
    mock.return_value = {
        "state": "running",
        "task_id": task.pk,
        "release_id": release.pk,
    }

    start_task(task.pk)

    task.refresh_from_db()

    assert task.state == "running"
    assert mock.call_count == 1
    mock.assert_called_with("start")


def test_start_task_fail(db, mocker):
    """
    Test that tasks that respond with anything other than 'running' will fail
    the release.
    """
    release = ReleaseFactory(state="running")
    service = ReleaseServiceFactory()
    task = ReleaseTaskFactory(
        release=release, release_service=service, state="initialized"
    )

    mock = mocker.patch("creator.releases.models.ReleaseTask._send_action")
    mock.return_value = {
        "state": "invalid state",
        "task_id": task.pk,
        "release_id": release.pk,
    }

    start_task(task.pk)

    task.refresh_from_db()

    assert task.state == "failed"
    assert mock.call_count == 1
    mock.assert_called_with("start")
