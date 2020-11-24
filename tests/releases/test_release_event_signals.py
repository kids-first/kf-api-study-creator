import pytest
from graphql_relay import to_global_id
from creator.releases.models import ReleaseEvent
from creator.releases.factories import ReleaseFactory


def test_release_signal_error(db):
    release = ReleaseFactory(state="running")
    release.failed()
    release.save()

    assert ReleaseEvent.objects.count() == 1
    assert ReleaseEvent.objects.first().event_type == "error"
