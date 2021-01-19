import pytz
from datetime import datetime

from creator.jobs.models import Job


def test_enqueued_at(mocker):
    """ Test that the enqueued_at property is computed correctly """

    class Scheduler:
        @property
        def connection(self):
            class Connection:
                def zscore(self, value, name):
                    return 999

            return Connection()

    mock_sched = mocker.patch("django_rq.get_scheduler")
    mock_sched.return_value = Scheduler()

    log = Job(scheduled=True)

    # Compute the expected DateTime from the seconds since epoch
    dt = datetime.fromtimestamp(999).replace(tzinfo=pytz.UTC)
    assert log.enqueued_at == dt


def test_enqueued_at_none(mocker):
    """ Test that a None response from redis is handled correctly """

    class Scheduler:
        @property
        def connection(self):
            class Connection:
                def zscore(self, value, name):
                    return None

            return Connection()

    mock_sched = mocker.patch("django_rq.get_scheduler")
    mock_sched.return_value = Scheduler()

    log = Job(scheduled=True)

    assert log.enqueued_at is None


def test_enqueued_at_not_scheduled(mocker):
    """ Test that non-scheduled jobs return None """
    log = Job(scheduled=False)

    assert log.enqueued_at is None
