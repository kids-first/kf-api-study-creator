import pytest
from creator.studies.factories import StudyFactory
from creator.studies.models import Study
from creator.slack import summary_post


def test_slack_notify_success(db, mocker, settings):
    """
    Test that the slack notify task operates correctly
    Only send slack notify to the studies has slack channel name
    and slack_notify value set the True
    """
    settings.SLACK_TOKEN = "ABC"

    study_with_slack = StudyFactory()
    study_no_slack = StudyFactory()
    study_disable_slack = StudyFactory()

    study_with_slack.slack_channel = "#sd_00000000"
    study_no_slack.slack_channel = None
    study_disable_slack.slack_notify = False

    study_with_slack.save()
    study_no_slack.save()
    study_disable_slack.save()

    notified_counts = summary_post()

    assert Study.objects.count() == 3
    assert notified_counts == 1
