import pytest
import datetime
from creator.studies.factories import StudyFactory
from creator.organizations.factories import OrganizationFactory
from creator.events.models import Event
from creator.studies.models import Study
from creator.slack import summary_post


def test_slack_notify_success(db, mocker, settings):
    """
    Test that the slack notify task operates correctly
    Only send slack notify to the studies has slack channel name
    and slack_notify value set the True
    """
    settings.SLACK_TOKEN = "ABC"

    mock_join = mocker.patch("creator.slack.WebClient.conversations_join")
    mock_post = mocker.patch("creator.slack.WebClient.chat_postMessage")
    mock_post.return_value = {"ok": True}
    mock_list = mocker.patch("creator.slack.WebClient.conversations_list")
    # Trimmed mock response based on example return in Slack docs:
    # https://api.slack.com/methods/conversations.list
    mock_list.return_value = {
        "ok": True,
        "channels": [
            {
                "id": "C012AB3CD",
                "name": "sd_00000000",
                "is_channel": True,
            },
        ],
        "response_metadata": {"next_cursor": "dGVhbTpDMDYxRkE1UEI="},
    }

    study_with_slack = StudyFactory()
    study_no_slack = StudyFactory()
    study_disable_slack = StudyFactory()

    study_with_slack.slack_channel = "sd_00000000"
    study_no_slack.slack_channel = None
    study_disable_slack.slack_notify = False

    study_with_slack.save()
    study_no_slack.save()
    study_disable_slack.save()

    event = Event(
        organization=OrganizationFactory(),
        event_type="SF_CRE",
        study=study_with_slack,
    )
    event.save()

    notified_counts = summary_post()

    assert Study.objects.count() == 3
    assert notified_counts == 1
    assert mock_join.call_count == 1
    assert mock_post.call_count == 1


def test_slack_notify_post_error(db, mocker, settings):
    """
    Test that issues sending messages to Slack are caught
    """
    settings.SLACK_TOKEN = "ABC"

    mock_logger = mocker.patch("creator.slack.logger.warning")
    mock_join = mocker.patch("creator.slack.WebClient.conversations_join")
    mock_post = mocker.patch("creator.slack.WebClient.chat_postMessage")
    mock_post.return_value = {"ok": False}
    mock_list = mocker.patch("creator.slack.WebClient.conversations_list")
    mock_list.return_value = {
        "ok": True,
        "channels": [
            {
                "id": "C012AB3CD",
                "name": "sd_00000000",
                "is_channel": True,
            },
        ],
    }

    study = StudyFactory()
    study.slack_channel = "sd_00000000"
    study.save()

    event = Event(
        organization=OrganizationFactory(), event_type="SF_CRE", study=study
    )
    event.save()

    notified_counts = summary_post()

    assert notified_counts == 1
    assert mock_join.call_count == 1
    assert mock_post.call_count == 1
    assert mock_logger.call_count == 1


def test_slack_notify_channel_not_found(db, mocker, settings):
    """
    Test that a warning is thrown when the channel cannot be found.
    """
    settings.SLACK_TOKEN = "ABC"

    mock_logger = mocker.patch("creator.slack.logger.warning")
    mock_post = mocker.patch("creator.slack.WebClient.chat_postMessage")
    mock_list = mocker.patch("creator.slack.WebClient.conversations_list")
    # Trimmed mock response based on example return in Slack docs:
    # https://api.slack.com/methods/conversations.list
    mock_list.return_value = {
        "ok": True,
        "channels": [],
        "response_metadata": {"next_cursor": "dGVhbTpDMDYxRkE1UEI="},
    }

    study = StudyFactory()

    study.slack_channel = "sd_00000000"
    study.slack_notify = True
    study.save()

    notified_counts = summary_post()

    assert mock_logger.call_count == 1
    assert mock_post.call_count == 0
    assert notified_counts == 1
