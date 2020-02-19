import pytest

from creator.files.models import Study
from creator.studies.factories import StudyFactory
from creator.events.models import Event
from creator.tasks import setup_bucket_task


def test_setup_bucket_success(db, mocker, settings):
    """
    Test that the setup task operates correctly when the setup succeeds
    """
    settings.FEAT_STUDY_BUCKETS_CREATE_BUCKETS = True
    settings.STUDY_BUCKETS_REGION = "us-east-1"
    settings.STUDY_BUCKETS_LOGGING_BUCKET = "bucket"
    settings.STUDY_BUCKETS_DR_LOGGING_BUCKET = "logging-bucket"
    settings.STUDY_BUCKETS_REPLICATION_ROLE = "arn:::"
    settings.STUDY_BUCKETS_INVENTORY_LOCATION = "bucket-metrics/inventory"

    study = StudyFactory()
    mock_setup = mocker.patch("creator.tasks.new_bucket")
    mock_setup.return_value = study

    assert Event.objects.count() == 0

    setup_bucket_task(study.kf_id)

    assert mock_setup.call_count == 1

    assert Event.objects.count() == 2
    assert Event.objects.filter(event_type="BK_STR").count() == 1
    assert Event.objects.filter(event_type="BK_SUC").count() == 1


def test_setup_bucket_no_study(db, mocker, settings):
    """
    Test that the setup task operates correctly when the setup succeeds
    """
    with pytest.raises(Study.DoesNotExist):
        setup_bucket_task("ABC")


def test_setup_bucket_fail(db, mocker, settings):
    """
    Test that the setup task operates correctly when the setup fails
    """
    settings.FEAT_STUDY_BUCKETS_CREATE_BUCKETS = True

    study = StudyFactory()
    mock_setup = mocker.patch("creator.tasks.new_bucket")
    mock_setup.side_effect = Exception("error making bucket")

    assert Event.objects.count() == 0

    with pytest.raises(Exception) as err:
        setup_bucket_task(study.kf_id)

    assert mock_setup.call_count == 1

    assert Event.objects.count() == 2
    assert Event.objects.filter(event_type="BK_STR").count() == 1
    assert Event.objects.filter(event_type="BK_ERR").count() == 1
