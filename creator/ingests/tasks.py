import logging

from creator.ingests.models import IngestRun
from creator.decorators import task

logger = logging.getLogger(__name__)


@task("ingest")
def run_ingest(ingest_run_id=None):
    """
    Run ingest process for a given set of files.
    """
    ingest_run = IngestRun.objects.get(ingest_run_id)
    logging.info(f"Preparing ingest run '{ingest_run.pk}' for processing")

    # Look for any ingest runs with identical input that are still in progress
    # and cancel them.
    # We could optionally scan for these before saving the database in the
    # startIngestRun mutation.
    others = IngestRun.objects.filter(
        state="running", input_hash=ingest_run.input_hash
    ).all()

    for running_ingest in others:
        logging.info(f"Canceling previous run '{running_ingest.pk}'")
        django_rq.enqueue(cancel_ingest, running_ingest.pk)

    # First we should update the ingest run's state so we know it's running
    ingest_run.start()
    ingest_run.save()

    try:
        # We can do the real ingest stuff here
        ingest_run.do_work()
    except Exception as err:
        logging.info(f"The ingest run '{ingest_run.pk}' failed: {err}")
        ingest_run.fail()
        ingest_run.save()
        raise

    logging.info(f"Finished processing ingest run '{ingest_run.pk}'")
    ingest_run.complete()
    ingest_run.save()


@task("ingest")
def cancel_ingest(ingest_run_id=None):
    """
    Cancel an ingest run
    """
    ingest_run = IngestRun.objects.get(ingest_run_id)
    logging.info(f"Preparing to cancel ingest run '{ingest_run.pk}'")

    # Maybe there's some work to do to clean up an ingest run that's in
    # progress?

    ingest_run.cancel()
    ingest_run.save()
