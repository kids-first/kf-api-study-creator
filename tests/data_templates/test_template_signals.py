import pytest

from creator.events.models import Event
from creator.data_templates.factories import (
    DataTemplateFactory,
    TemplateVersionFactory,
)


@pytest.mark.parametrize(
    "event_type,verb",
    [
        ("DT_CRE", "created"),
        ("DT_UPD", "updated"),
        ("DT_DEL", "deleted"),
    ],
)
def test_data_template_signals(db, event_type, verb):
    """
    Test Data Template signals for create, update, delete
    """
    dt = DataTemplateFactory()

    if verb == "updated":
        dt.name = "My new name"
        dt.save()

    elif verb == "deleted":
        dt.delete()

    assert Event.objects.filter(event_type=event_type).count() == 1


@pytest.mark.parametrize(
    "event_type,verb",
    [
        ("TV_CRE", "created"),
        ("TV_UPD", "updated"),
        ("TV_DEL", "deleted"),
    ],
)
def test_template_version_signals(db, event_type, verb):
    """
    Test Template Version signals for create, update, delete
    """
    dt = DataTemplateFactory()
    tv = TemplateVersionFactory(data_template=dt)

    if verb == "created":
        event_count = 1

    elif verb == "updated":
        tv.description = "My new name"
        tv.save()
        # Count is 2 not 1, bc the factory creates AND updates the obj on
        # creation
        event_count = 2

    elif verb == "deleted":
        tv.delete()
        event_count = 1

    events = Event.objects.filter(event_type=event_type).all()
    assert len(events) == event_count
    etypes = {e.event_type for e in events}
    assert event_type in etypes
