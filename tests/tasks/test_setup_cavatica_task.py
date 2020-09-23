import pytest
from django.contrib.auth import get_user_model

from creator.files.models import Study
from creator.studies.factories import StudyFactory
from creator.events.models import Event
from creator.tasks import setup_cavatica_task

User = get_user_model()


def test_setup_cavatica_success(db, mocker, settings):
    """
    Test that the setup task operates correctly when the setup succeeds
    """
    settings.FEAT_BUCKETSERVICE_CREATE_BUCKETS = True
    settings.BUCKETSERVICE_URL = "http://bucketservice"

    study = StudyFactory()
    mock_setup = mocker.patch("creator.tasks.setup_cavatica")
    mock_setup.return_value = study

    assert Event.objects.count() == 0

    setup_cavatica_task(study.kf_id, [], User.objects.first())

    assert mock_setup.call_count == 1

    assert Event.objects.count() == 2
    assert Event.objects.filter(event_type="PR_STR").count() == 1
    assert Event.objects.filter(event_type="PR_SUC").count() == 1


def test_setup_cavatica_no_study(db, mocker, settings):
    """
    Test that correct exception is raised if the study does not exist
    """
    with pytest.raises(Study.DoesNotExist):
        setup_cavatica_task("ABC", [], "abc")


def test_setup_cavatica_no_user(db, mocker, settings):
    """
    Test that correct exception is raised if the study does not exist
    """
    study = StudyFactory()
    mock_setup = mocker.patch("creator.tasks.setup_cavatica")

    setup_cavatica_task(study.kf_id, [], "abc")

    mock_setup.assert_called_with(study, workflows=[], user=None)


def test_setup_cavatica_fail(db, mocker, settings):
    """
    test that the setup task operates correctly when the setup fails
    """
    settings.feat_bucketservice_create_buckets = True
    settings.bucketservice_url = "http://bucketservice"

    study = StudyFactory()
    mock_setup = mocker.patch("creator.tasks.setup_cavatica")
    mock_setup.side_effect = Exception("error making cavatica")

    assert Event.objects.count() == 0

    with pytest.raises(Exception):
        setup_cavatica_task(study.kf_id, [], "abc")

    assert mock_setup.call_count == 1

    assert Event.objects.count() == 2
    assert Event.objects.filter(event_type="PR_STR").count() == 1
    assert Event.objects.filter(event_type="PR_ERR").count() == 1
