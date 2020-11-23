import pytest
from graphql_relay import to_global_id

from creator.studies.factories import StudyFactory
from creator.releases.factories import (
    ReleaseFactory,
    ReleaseTaskFactory,
    ReleaseServiceFactory,
)

from creator.releases.models import Release, ReleaseTask
from creator.releases.tasks import cancel_release, cancel_task


def test_cancel_release_no_tasks(db):
    """
    Test that the cancel_release task immediately goes to 'canceled' when there
    are no services in the release
    """
    release = ReleaseFactory(state="canceling")

    cancel_release(release_id=release.pk)

    release.refresh_from_db()

    assert release.state == "canceled"


def test_cancel_release_with_tasks(db, mocker):
    """
    Test that cancel_release queues cancel_task jobs for each task
    """
    mock_rq = mocker.patch("rq.Queue.enqueue")

    release = ReleaseFactory(state="canceling")
    service = ReleaseServiceFactory()
    task = ReleaseTaskFactory(
        release=release, release_service=service, state="initialized"
    )

    cancel_release(release_id=release.pk)

    release.refresh_from_db()

    assert release.state == "canceling"
    assert mock_rq.call_count == 1
    mock_rq.assert_called_with(cancel_task, task_id=task.pk, ttl=60)


def test_cancel_failed_release_with_no_tasks(db, mocker):
    """
    Test that the release moves directly to failed
    """
    release = ReleaseFactory(state="canceling")
    service = ReleaseServiceFactory()

    cancel_release(release_id=release.pk, failed=True)

    release.refresh_from_db()

    assert release.state == "failed"


def test_cancel_task(db, mocker):
    """
    Test that the cancel_task updates correctly
    """
    release = ReleaseFactory(state="canceling")
    service = ReleaseServiceFactory()
    task = ReleaseTaskFactory(
        release=release, release_service=service, state="initialized"
    )

    mock = mocker.patch("creator.releases.models.ReleaseTask._send_action")
    mock.return_value = {
        "task_id": task.pk,
        "release_id": release.pk,
        "state": "canceled",
    }

    cancel_task(task_id=task.pk)

    task.refresh_from_db()

    assert task.state == "canceled"


def test_cancel_task_failed(db, mocker):
    """
    Test that tasks are failed if they fail to cancel
    """
    release = ReleaseFactory(state="canceling")
    service = ReleaseServiceFactory()
    task = ReleaseTaskFactory(
        release=release, release_service=service, state="initialized"
    )

    mock = mocker.patch("creator.releases.models.ReleaseTask._send_action")
    mock.side_effect = Exception("Problem sending action")

    cancel_task(task_id=task.pk)

    task.refresh_from_db()

    assert task.state == "failed"
