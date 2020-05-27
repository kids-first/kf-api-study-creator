import pytest
from creator.studies.factories import StudyFactory
from creator.studies.models import Study
from creator.events.models import Event
from creator.tasks import setup_slack_task


def test_setup_slack_success(db, mocker, settings):
    """
    Test that the setup task operates correctly when the setup succeeds
    """
    settings.FEAT_SLACK_CREATE_CHANNELS = True
    settings.SLACK_TOKEN = "ABC"

    study = StudyFactory()
    mock_setup = mocker.patch("creator.tasks.setup_slack")

    assert Event.objects.count() == 0

    setup_slack_task(study.kf_id)

    assert mock_setup.call_count == 1

    assert Event.objects.count() == 2
    assert Event.objects.filter(event_type="SL_STR").count() == 1
    assert Event.objects.filter(event_type="SL_SUC").count() == 1


def test_setup_slack_no_study(db, mocker, settings):
    """
    Test that correct exception is raised if the study does not exist
    """
    with pytest.raises(Study.DoesNotExist):
        setup_slack_task("ABC")


def test_setup_slack_fail(db, mocker, settings):
    """
    Test that the setup task operates correctly when the setup fails
    """
    settings.FEAT_SLACK_CREATE_CHANNELS = True
    settings.SLACK_TOKEN = "ABC"

    study = StudyFactory()
    mock_setup = mocker.patch("creator.tasks.setup_slack")
    mock_setup.side_effect = Exception("error making channel")

    assert Event.objects.count() == 0

    setup_slack_task(study.kf_id)

    assert mock_setup.call_count == 1

    assert Event.objects.count() == 2
    assert Event.objects.filter(event_type="SL_STR").count() == 1
    assert Event.objects.filter(event_type="SL_ERR").count() == 1
