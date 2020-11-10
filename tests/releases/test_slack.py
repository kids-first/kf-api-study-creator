import pytest
from creator.releases.slack import send_status_notification
from creator.releases.factories import ReleaseFactory
from creator.studies.factories import StudyFactory


def test_slack_disabled(db, mocker, settings):
    """
    Test that messages aren't sent if release notifications are turned off
    """
    mock = mocker.patch("creator.releases.slack.WebClient.chat_postMessage")

    settings.FEAT_SLACK_SEND_RELEASE_NOTIFICATIONS = False

    release = ReleaseFactory(state="running")

    send_status_notification(release.pk)

    assert mock.call_count == 0


def test_slack_enabled(db, mocker, settings):
    """
    Test that messages are sent if the notifications are turned on
    """
    mock = mocker.patch("creator.releases.slack.WebClient.chat_postMessage")

    settings.FEAT_SLACK_SEND_RELEASE_NOTIFICATIONS = True

    studies = StudyFactory.create_batch(3)
    release = ReleaseFactory(state="running", studies=studies)

    send_status_notification(release.pk)

    assert mock.call_count == 1


@pytest.mark.parametrize("state", ["initializing", "waiting"])
def test_slack_ignore_states(db, mocker, settings, state):
    """
    Test that notifications are not sent for releases in waiting or
    initializing states
    """
    mock = mocker.patch("creator.releases.slack.WebClient.chat_postMessage")

    settings.FEAT_SLACK_SEND_RELEASE_NOTIFICATIONS = True

    release = ReleaseFactory(state=state)

    send_status_notification(release.pk)

    assert mock.call_count == 0
