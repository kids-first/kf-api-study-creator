import pytest

from django.contrib.auth import get_user_model

from creator.data_reviews.factories import DataReview
from creator.data_reviews.models import State
from creator.events.models import Event

User = get_user_model()


@pytest.mark.parametrize(
    "start_state,state_transition_method,expected_msg",
    [
        (State.NOT_STARTED, None, None),
        (State.NOT_STARTED, "start", "started a data review"),
        (State.IN_REVIEW, "wait_for_updates", "is waiting"),
        (State.WAITING, "receive_updates", "received file updates"),
        (State.IN_REVIEW, "close", "closed the data review"),
        (State.CLOSED, "reopen", "re-opened the data review"),
        (State.IN_REVIEW, "approve", "completed the data review"),
    ],
)
def test_state_update_signals(
    db, clients, start_state, state_transition_method, expected_msg
):
    """
    Test that correct events are fired on DataReview state transitions
    """
    event_count_before = Event.objects.count()
    creator = User.objects.first()
    dr = DataReview(creator=creator, state=start_state)
    dr.save()

    if state_transition_method:
        transition = getattr(dr, state_transition_method)
        transition()
        dr.save()
        e = Event.objects.filter(data_review__pk=dr.pk).all()[0]
        assert expected_msg in e.description
    else:
        assert event_count_before == Event.objects.count()
