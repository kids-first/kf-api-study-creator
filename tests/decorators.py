import pytest
from creator.decorators import task
from creator.jobs.models import Job, JobLog
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


def test_release_job_log(db):
    """
    Test that a task with a specified release id attaches the log to the
    appropriate release
    """

    @task("myjob")
    def my_job(release_id):
        pass

    release = ReleaseFactory()

    my_job(release_id=release.pk)

    release.refresh_from_db()
    assert Job.objects.count() == 1
    assert JobLog.objects.count() == 1
    assert Job.objects.first().scheduled is False
    assert Job.objects.first().name == "myjob"
    assert release.job_log == JobLog.objects.first()


def test_task_job_log(db):
    """
    Test that a task with a specified task id attaches the log to the
    appropriate task
    """

    @task("myjob")
    def my_job(task_id):
        pass

    release_task = ReleaseTaskFactory()

    my_job(task_id=release_task.pk)

    release_task.refresh_from_db()
    assert Job.objects.count() == 1
    assert JobLog.objects.count() == 1
    assert Job.objects.first().scheduled is False
    assert Job.objects.first().name == "myjob"
    assert release_task.job_log == JobLog.objects.first()
