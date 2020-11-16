import pytest
from rq.worker import WorkerStatus
from rq.job import NoSuchJobError, JobStatus
from creator.utils import stop_job


def test_stop_job_not_found(mocker):
    """
    Test stop_job with a non-existing job and default queue
    """
    mock_queue = mocker.patch("creator.utils.django_rq.get_queue")
    mock_job = mocker.patch("creator.utils.Job")
    mock_job.fetch.side_effect = [NoSuchJobError]
    stop_job("foo")
    assert mock_job.fetch.call_count == 1
    assert mock_queue.call_count == 1
    mock_job.reset_mock()


@pytest.mark.parametrize("delete", [True, False])
@pytest.mark.parametrize(
    "job_status",
    [
        JobStatus.FAILED,
        JobStatus.FINISHED,
        JobStatus.QUEUED,
        JobStatus.DEFERRED,
        JobStatus.STARTED,
    ],
)
def test_stop_jobs(mocker, job_status, delete):
    """
    Test stop job on failed, finished, queued, deferred, and started jobs
    """

    class Queue:
        def __init__(self):
            self.connection = "redis connection object"
            self.name = "redis queue"

    class Job:
        def __init__(self):
            self.id = "foo"

    class Worker:
        def __init__(self):
            self.state = WorkerStatus.BUSY
            self.name = "worker"

        @classmethod
        def all(cls, **kwargs):
            return [cls()]

        def get_current_job(self):
            return Job()

    mock_queue = mocker.patch("creator.utils.django_rq.get_queue")
    mock_queue.return_value = Queue()
    mock_job = mocker.patch("creator.utils.Job")
    mock_job.get_status.return_value = job_status
    mock_job.fetch.return_value = mock_job
    mocker.patch("creator.utils.Worker.all", Worker.all)
    mock_kill = mocker.patch("creator.utils.send_kill_horse_command")

    stop_job("foo", mock_queue(), delete)
    assert mock_job.get_status.call_count == 1

    if job_status in {JobStatus.QUEUED, JobStatus.DEFERRED}:
        assert mock_job.cancel.call_count == 1

    if job_status == JobStatus.STARTED:
        assert mock_kill.call_count == 1

    if delete:
        mock_job.delete.call_count == 1
