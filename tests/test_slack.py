import pytest
from creator.studies.factories import StudyFactory
from creator.slack import setup_slack


def test_setup_slack(db, mocker):
    """
    Check that the correct operations are applied to create a channel.
    """
    study = StudyFactory()
    channel_name = study.kf_id.lower().replace("_", "-")

    mock_client = mocker.patch("creator.slack.WebClient")
    mock_client().conversations_create.return_value = {
        "channel": {"id": "ABC", "name": channel_name}
    }

    assert study.slack_channel is None

    setup_slack(study)

    assert study.slack_channel == channel_name

    # Channel is created
    mock_client().conversations_create.assert_called_with(
        name=study.kf_id.lower().replace("_", "-")
    )

    # Topic is set
    assert mock_client().conversations_setTopic.call_count == 1

    # Message is pinned
    assert mock_client().chat_postMessage.call_count == 1
    assert mock_client().pins_add.call_count == 1

    # Users are invited
    assert mock_client().conversations_invite.call_count == 1
