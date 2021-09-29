import os
import pytest
from creator.decorators import task
from creator.jobs.models import Job, JobLog
from creator.studies.models import Study
from creator.studies.factories import StudyFactory
from creator.releases.models import Release
from creator.releases.factories import ReleaseFactory, ReleaseTaskFactory


def test_new_job(db):
    @task("myjob")
    def my_job():
        pass

    my_job()

    assert Job.objects.count() == 1
    assert JobLog.objects.count() == 1
    assert Job.objects.first().scheduled is False
    assert Job.objects.first().name == "myjob"
    assert os.path.exists(JobLog.objects.first().log_file.path)


def test_related_models_by_pk(db):
    """
    Test that passing a release's id will cause the relevant release to have
    a job log attached to it
    """

    @task("myjob", related_models={Release: "release"})
    def my_job(release):
        pass

    release = ReleaseFactory()

    my_job(release=release.pk)

    release.refresh_from_db()
    assert Job.objects.count() == 1
    assert JobLog.objects.count() == 1
    assert Job.objects.first().scheduled is False
    assert Job.objects.first().name == "myjob"
    assert release.job_log == JobLog.objects.first()


def test_related_models_by_instance(db):
    """
    Test that passing an instance of the model directly will cause a job log
    to be attached to it
    """

    @task("myjob", related_models={Release: "release"})
    def my_job(release):
        pass

    release = ReleaseFactory()

    my_job(release=release)

    release.refresh_from_db()
    assert Job.objects.count() == 1
    assert JobLog.objects.count() == 1
    assert Job.objects.first().scheduled is False
    assert Job.objects.first().name == "myjob"
    assert release.job_log == JobLog.objects.first()


def test_related_models_no_property(db, mocker):
    """
    Test that models that do not have a job_log field do not have job logs
    attached to them.
    """

    @task("myjob", related_models={Study: "study"})
    def my_job(study):
        pass

    study = StudyFactory()
    mock = mocker.patch("creator.decorators.logger.warning")

    my_job(study=study)

    assert mock.call_count == 1
    assert "must have a" in mock.call_args_list[0].args[0]


def test_related_models_arg_not_found(db, mocker):
    """
    Test that no relations are formed if the specified argument cant' be found
    """

    @task("myjob", related_models={Release: "release_id"})
    def my_job(release):
        pass

    mock = mocker.patch("creator.decorators.logger.warning")

    release = ReleaseFactory()

    my_job(release=release)

    assert mock.call_count == 1
    assert "Could not find" in mock.call_args_list[0].args[0]
