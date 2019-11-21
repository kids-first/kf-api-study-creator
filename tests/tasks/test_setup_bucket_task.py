import pytest

from creator.files.models import Study
from creator.studies.factories import StudyFactory
from creator.events.models import Event
from creator.tasks import setup_bucket_task


def test_setup_bucket_success(db, mocker, settings):
    """
    Test that the setup task operates correctly when the setup succeeds
    """
    settings.FEAT_BUCKETSERVICE_CREATE_BUCKETS = True
    settings.BUCKETSERVICE_URL = "http://bucketservice"

    study = StudyFactory()
    mock_setup = mocker.patch("creator.tasks.setup_bucket")
    mock_setup.return_value = study

    assert Event.objects.count() == 0

    setup_bucket_task(study.kf_id)

    assert mock_setup.call_count == 1

    assert Event.objects.count() == 2
    assert Event.objects.filter(event_type="BK_STR").count() == 1
    assert Event.objects.filter(event_type="BK_SUC").count() == 1


def test_setup_bucket_fail(db, mocker, settings):
    """
    Test that the setup task operates correctly when the setup fails
    """
    settings.FEAT_BUCKETSERVICE_CREATE_BUCKETS = True
    settings.BUCKETSERVICE_URL = "http://bucketservice"

    study = StudyFactory()
    mock_setup = mocker.patch("creator.tasks.setup_bucket")
    mock_setup.side_effect = Exception("error making bucket")

    assert Event.objects.count() == 0

    setup_bucket_task(study.kf_id)

    assert mock_setup.call_count == 1

    assert Event.objects.count() == 2
    assert Event.objects.filter(event_type="BK_STR").count() == 1
    assert Event.objects.filter(event_type="BK_ERR").count() == 1
