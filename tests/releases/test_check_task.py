import pytest

from creator.releases.tasks import scan_tasks
from creator.releases.factories import ReleaseFactory, ReleaseTaskFactory


def test_scan_tasks(db, mocker):
    """
    Check that only tasks that are in a non-terminal state get state checks
    queued on them.
    """
    mock_rq = mocker.patch("rq.Queue.enqueue")

    release = ReleaseFactory()
    states = [
        "waiting",
        "initializing",
        "initialized",
        "running",
        "staged",
        "publishing",
        "published",
        "canceled",
        "canceling",
        "failed",
        "rejected",
    ]
    for state in states:
        ReleaseTaskFactory(state=state, release=release)

    scan_tasks()

    assert mock_rq.call_count == 7


@pytest.mark.parametrize(
    "our_state,service_state",
    [
        ("running", "running"),
        ("publishing", "publishing"),
        ("waiting", "waiting"),
        ("canceling", "canceling"),
        ("running", "staged"),
        ("publishing", "published"),
        ("waiting", "failed"),
        ("running", "failed"),
        ("publishing", "failed"),
        ("canceling", "failed"),
    ],
)
def test_check_task_state(db, mocker, our_state, service_state):
    """
    Check that the task's state gets updated to reflect the service's state
    """
    release = ReleaseFactory()
    task = ReleaseTaskFactory(state=our_state, release=release)

    mock_state = mocker.patch(
        "creator.releases.models.ReleaseTask._send_action"
    )
    mock_state.return_value = {
        "task_id": task.pk,
        "release_id": release.pk,
        "state": service_state,
    }

    task.check_state()

    assert task.state == service_state


@pytest.mark.parametrize(
    "our_state,service_state",
    [
        ("initializing", "running"),
        ("staged", "publishing"),
        ("running", "canceling"),
    ],
)
def test_check_task_invalid_states(db, mocker, our_state, service_state):
    """
    We should never observe these transitions happen on the service without
    us initializing them.
    """
    release = ReleaseFactory()
    task = ReleaseTaskFactory(state=our_state, release=release)

    mock_state = mocker.patch(
        "creator.releases.models.ReleaseTask._send_action"
    )
    mock_state.return_value = {
        "task_id": task.pk,
        "release_id": release.pk,
        "state": service_state,
    }

    with pytest.raises(ValueError):
        task.check_state()

    assert task.state == our_state
