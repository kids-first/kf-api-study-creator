import pytest

from creator.releases.tasks import scan_releases
from creator.releases.factories import ReleaseFactory


def test_scan_releases(db, mocker):
    """
    Check that only releases in action are queued for status checks.
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
    ]
    for state in states:
        ReleaseFactory(state=state)

    scan_releases()

    assert mock_rq.call_count == 5
