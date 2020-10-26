import pytest

from creator.releases.models import Release, ReleaseTask
from creator.studies.factories import StudyFactory
from creator.releases.tasks import check_release
from creator.releases.factories import (
    ReleaseFactory,
    ReleaseTaskFactory,
    ReleaseServiceFactory,
)


@pytest.mark.parametrize(
    "task_states,release_source_state,release_target_state",
    [
        ((), "initializing", "running"),
        ((), "publishing", "published"),
        (("initializing", "initializing"), "initializing", "initializing"),
        (("initializing", "initialized"), "initializing", "initializing"),
        (("initialized", "initialized"), "initializing", "running"),
        (("initializing", "canceling"), "initializing", "canceling"),
        (("initializing", "canceled"), "initializing", "canceling"),
        (("initializing", "failed"), "initializing", "canceling"),
        (("running", "running"), "running", "running"),
        (("running", "running"), "running", "running"),
        (("running", "canceling"), "running", "canceling"),
        (("running", "canceled"), "running", "canceling"),
        (("running", "failed"), "running", "canceling"),
        (("running", "staged"), "running", "running"),
        (("staged", "canceling"), "running", "canceling"),
        (("staged", "canceled"), "running", "canceling"),
        (("staged", "failed"), "running", "canceling"),
        (("staged", "staged"), "running", "staged"),
        (("publishing", "publishing"), "publishing", "publishing"),
        (("publishing", "canceling"), "publishing", "canceling"),
        (("publishing", "canceled"), "publishing", "canceling"),
        (("publishing", "failed"), "publishing", "canceling"),
        (("publishing", "published"), "publishing", "publishing"),
        (("published", "published"), "publishing", "published"),
    ],
)
def test_check_release(
    db, mocker, task_states, release_source_state, release_target_state
):
    """
    Check that the check_release task correctly updates the release's state.
    """
    mock_rq = mocker.patch("creator.releases.mutations.django_rq.enqueue")

    release = ReleaseFactory(state=release_source_state)
    for state in task_states:
        task = ReleaseTaskFactory(state=state, release=release)

    check_release(release.pk)

    release.refresh_from_db()

    assert release.state == release_target_state
