import time
import logging
import django_rq
from rq.job import NoSuchJobError, JobStatus, Job
from rq.command import send_kill_horse_command
from rq.worker import Worker, WorkerStatus

logger = logging.getLogger(__name__)
WAIT_FOR_FAIL_TIME = 0.25


def stop_job(job_id, queue=None, delete=True):
    """
    Stop a running rq job and optionally delete the job from its queue
    and rq registries.

    NOTE: This method may not be needed after this
    https://github.com/rq/rq/issues/1371 is implemented

    For jobs that have finished/failed, do nothing
    For jobs that are queued/deferred cancel or delete them (see rq.job.Job)
    For jobs that have started, kill the worker horse executing the job

    If delete is True, remove the job from its queue, all rq registries,
    and from redis

    If delete is False just remove the job from its queue

    :param job_id: The id of the job: rq.Job.id
    :type job_id: str
    :param queue: The queue the job was submitted to
    :type queue: rq.Queue
    :param delete: whether to delete or cancel the job
    :type delete: bool
    """
    logger.info(f"Preparing to stop redis job {job_id}")

    # Find rq job
    if not queue:
        queue = django_rq.get_queue()

    try:
        redis_job = Job.fetch(job_id, connection=queue.connection)
    except NoSuchJobError:
        logger.info(f"Job {job_id} not found, aborting")
        return

    status = redis_job.get_status()

    # Skip jobs that have failed or are finished
    if status in {JobStatus.FAILED, JobStatus.FINISHED}:
        logger.info(f"Job {job_id} already complete, aborting")
        return

    # Cancel jobs that haven't started yet
    if status in {JobStatus.QUEUED, JobStatus.DEFERRED}:
        logger.info(
            f"Cancel job {job_id} by removing it from queue: {queue.name}"
        )
        redis_job.cancel()
        return
    # Kill running jobs
    else:
        for worker in Worker.all(queue=queue):
            print(worker.state, worker.get_current_job().id)
            if (worker.state == WorkerStatus.BUSY) and (
                worker.get_current_job().id == job_id
            ):
                logger.info(f"Killing job {job_id}")
                send_kill_horse_command(queue.connection, worker.name)

    # Delete job from failed job registry
    if delete:
        time.sleep(WAIT_FOR_FAIL_TIME)
        logger.info(
            f"Delete job {job_id} by removing it from queue: "
            f"{queue.name} and all job registries"
        )
        redis_job.delete()
