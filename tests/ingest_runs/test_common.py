import pytest

from django.contrib.auth import get_user_model

from creator.ingest_runs.common.model import (
    hash_versions,
    State,
    camel_to_snake,
)
from creator.ingest_runs.common.mutations import (
    cancel_duplicate_ingest_processes
)
from creator.files.models import Version
from creator.ingest_runs.models import (
    IngestRun,
    ValidationRun,
)
from creator.ingest_runs.factories import (
    IngestRunFactory,
    ValidationRunFactory,
)
from creator.events.models import Event
from creator.ingest_runs.tasks import cancel_ingest, cancel_validation

User = get_user_model()


def test_hash_versions(db, clients, prep_file):
    """
    Test hash_versions
    """
    # Create some data
    versions = []
    for i in range(3):
        study_id, file_id, version_id = prep_file(authed=True)
        versions.append(version_id)

    # Hashes for two version lists, regardless of order, should be equal
    h1 = hash_versions(versions)
    assert h1
    assert h1 == hash_versions(versions[::-1])

    # Hashes for two different version lists should be different
    assert h1 != hash_versions(versions[0:1])


@pytest.mark.parametrize(
    "start_state,state_transition_method,expected_msg",
    [
        (State.NOT_STARTED, None, None),
        (State.NOT_STARTED, "initialize", "started"),
        (State.INITIALIZING, "start", "is running"),
        (State.RUNNING, "complete", "completed"),
        (State.RUNNING, "start_cancel", "requested to cancel"),
        (State.CANCELING, "cancel", "canceled"),
        (State.RUNNING, "fail", "failed"),
        (State.NOT_STARTED, "fail", "failed"),
        (State.INITIALIZING, "fail", "failed"),
        (State.CANCELING, "fail", "failed"),
    ],
)
@pytest.mark.parametrize(
    "ingest_process_cls",
    [
        ValidationRun,
        IngestRun,
    ]
)
def test_ingest_process_states(
    db, mocker, ingest_process_cls, start_state, state_transition_method,
    expected_msg
):
    """
    Test that correct events are fired on ingest process state transitions
    """
    mock_stop_job = mocker.patch(
        "creator.ingest_runs.common.model.stop_job"
    )
    creator = User.objects.first()
    obj = ingest_process_cls(creator=creator, state=start_state)
    obj.save()

    event_count_before = Event.objects.count()
    if state_transition_method:
        # Execute state transition
        transition = getattr(obj, state_transition_method)
        transition()
        obj.save()

        # Check start/stop times
        if state_transition_method == "initialize":
            assert obj.started_at
        elif state_transition_method in {"cancel", "fail", "complete"}:
            assert obj.stopped_at

        # Check event
        foreign_key = camel_to_snake(ingest_process_cls.__name__)
        kwargs = {foreign_key: obj.pk}
        e = Event.objects.filter(**kwargs).all()[0]
        assert expected_msg in e.description
        assert foreign_key.replace("_", " ") in e.description.lower()
        # Cancel method includes a call to stop_job
        if state_transition_method == "cancel":
            mock_stop_job.assert_called_with(
                str(obj.pk), queue=obj.queue, delete=True
            )
    else:
        assert event_count_before == Event.objects.count()


@pytest.mark.parametrize(
    "factory,cancel_task,state",
    [
        (IngestRunFactory, cancel_ingest, State.NOT_STARTED),
        (IngestRunFactory, cancel_ingest, State.INITIALIZING),
        (IngestRunFactory, cancel_ingest, State.RUNNING),
        (ValidationRunFactory, cancel_validation, State.NOT_STARTED),
        (ValidationRunFactory, cancel_validation, State.INITIALIZING),
        (ValidationRunFactory, cancel_validation, State.RUNNING),
    ]
)
def test_cancel_duplicate_ingest_processes(
    db, mocker, clients, prep_file, factory, cancel_task, state
):
    """
    Test cancel_duplicate_ingest_processes
    """
    mock_queue = mocker.patch(
        "creator.ingest_runs.common.model.IngestProcess.queue"
    )
    # Create an ingest process with some versions
    versions = []
    for i in range(2):
        study_id, file_id, version_id = prep_file(authed=True)
        versions.append(Version.objects.get(pk=version_id))
    process = factory(versions=versions[0:1], state=state)
    version_ids = [v.kf_id for v in versions]

    # Ingest processes with same set of versions are duplicates and should be
    # canceled
    canceled_any = cancel_duplicate_ingest_processes(
        version_ids[0:1], process.__class__, cancel_task
    )
    process.refresh_from_db()

    assert canceled_any
    assert process.state == State.CANCELING
    mock_queue.enqueue.assert_called_with(
        cancel_task, args=(process.id,)
    )
    mock_queue.reset_mock()

    # Ingest processes with different versions won't be canceled
    canceled_any = cancel_duplicate_ingest_processes(
        version_ids, process.__class__, cancel_task
    )
    mock_queue.enqueue.call_count == 0
    assert (not canceled_any)
