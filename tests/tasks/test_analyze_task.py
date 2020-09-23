import pytest
from creator.jobs.models import Job
from creator.studies.factories import StudyFactory
from creator.files.factories import VersionFactory, FileFactory
from creator.studies.models import Study
from creator.files.models import Version
from creator.events.models import Event
from creator.tasks import analyzer_task


def versions(db):
    study = StudyFactory()
    file = FileFactory()
    versions = VersionFactory.create_batch(5, root_file=file)
    return versions


def test_analyzer_task_success(db, mocker, versions):
    """
    """
    job = Job(name="analyzer")
    job.save()

    mock = mocker.patch("creator.tasks.analyze_version")

    analyzer_task()

    job.refresh_from_db()
    assert job.last_run is not None
    assert job.failing is False
    assert job.last_error == ""
    assert mock.call_count == Version.objects.count()


def test_analyzer_task_error(db, mocker, versions):
    """
    test that errors are logged correctly
    """
    job = Job(name="analyzer")
    job.save()

    mock = mocker.patch("creator.tasks.analyze_version")
    mock.side_effect = Exception("error occurred")

    with pytest.raises(Exception):
        analyzer_task()

    job.refresh_from_db()
    assert job.failing
    assert "Failed to analyze" in job.last_error
    assert mock.call_count == Version.objects.count()


def test_analyzer_task_inactive(db, mocker, versions):
    """
    test that errors are logged correctly
    """
    job = Job(name="analyzer", active=False)
    job.save()

    mock = mocker.patch("creator.tasks.analyze_version")

    analyzer_task()

    job.refresh_from_db()
    assert mock.call_count == 0
