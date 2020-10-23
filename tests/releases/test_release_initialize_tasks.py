import pytest
from graphql_relay import to_global_id

from creator.studies.factories import StudyFactory
from creator.releases.factories import (
    ReleaseFactory,
    ReleaseTaskFactory,
    ReleaseServiceFactory,
)

from creator.releases.models import Release, ReleaseTask
from creator.releases.tasks import initialize_release, initialize_task


def test_initialize_release_no_tasks(db, mocker):
    """
    Test that the initialize_release task immediately moves the release
    to 'running' if there are no services in the release.
    """
    mock_rq = mocker.patch("creator.releases.tasks.django_rq.enqueue")

    release = ReleaseFactory(state="initializing")

    initialize_release(release.pk)

    release.refresh_from_db()

    assert release.state == "running"
    assert mock_rq.call_count == 0


def test_initialize_release_with_tasks(db, mocker):
    """
    Test that the initialize_release task enqueues tasks to initialize each
    service in the release.
    """
    mock_rq = mocker.patch("creator.releases.tasks.django_rq.enqueue")

    release = ReleaseFactory(state="initializing")
    service = ReleaseServiceFactory()
    task = ReleaseTaskFactory(release=release, release_service=service)

    initialize_release(release.pk)

    release.refresh_from_db()

    assert release.state == "initializing"
    assert mock_rq.call_count == 1


def test_initialize_task_successful(db, mocker):
    """
    Test that the initialize_task task properly moves the task's state foreward
    """
    release = ReleaseFactory(state="initializing")
    service = ReleaseServiceFactory()
    task = ReleaseTaskFactory(release=release, release_service=service)

    mock = mocker.patch("creator.releases.models.ReleaseTask._send_action")
    mock.return_value = {
        "state": "initialized",
        "task_id": task.pk,
        "release_id": release.pk,
    }

    initialize_task(task.pk)

    task.refresh_from_db()

    assert task.state == "initialized"
    assert mock.call_count == 1
    mock.assert_called_with("initialize")


def test_initialize_task_rejected(db, mocker):
    """
    Test that tasks that respond with anything other than 'initialized' cancel
    the release.
    """
    release = ReleaseFactory(state="initializing")
    service = ReleaseServiceFactory()
    task = ReleaseTaskFactory(release=release, release_service=service)

    mock = mocker.patch("creator.releases.models.ReleaseTask._send_action")
    mock.return_value = {
        "state": "invalid state",
        "task_id": task.pk,
        "release_id": release.pk,
    }

    initialize_task(task.pk)

    task.refresh_from_db()

    assert task.state == "rejected"
    assert mock.call_count == 1
    mock.assert_called_with("initialize")
