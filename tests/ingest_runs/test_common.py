import pytest

from django.contrib.auth import get_user_model

from creator.ingest_runs.common.model import (
    hash_versions,
    State,
    camel_to_snake,
)
from creator.ingest_runs.models import (
    # ValidationRun,
    IngestRun,
)
from creator.files.models import Version
from creator.events.models import Event

User = get_user_model()


def test_hash_versions(db, clients, prep_file):
    """
    Test hash_versions
    """
    # Create some data
    versions = []
    for i in range(3):
        study_id, file_id, version_id = prep_file(authed=True)
        versions.append(Version.objects.get(pk=version_id))

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
        (State.NOT_STARTED, "start", "started"),
        (State.RUNNING, "complete", "completed"),
        (State.RUNNING, "cancel", "canceled"),
        (State.RUNNING, "fail", "failed"),
    ],
)
@pytest.mark.parametrize(
    "ingest_process_cls",
    [
        # ValidationRun,
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
        if state_transition_method == "start":
            assert obj.started_at
        else:
            assert obj.stopped_at

        # Check event
        foreign_key = camel_to_snake(ingest_process_cls.__name__)
        kwargs = {foreign_key: obj.pk}
        e = Event.objects.filter(**kwargs).all()[0]
        assert expected_msg in e.description
        assert foreign_key.replace("_", " ") in e.description.lower()
        if state_transition_method == "cancel":
            mock_stop_job.assert_called_with(
                str(obj.pk), queue=obj.queue, delete=True
            )
    else:
        assert event_count_before == Event.objects.count()
