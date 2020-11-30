import django_rq
import logging

from django.core.exceptions import ValidationError

from creator.decorators import task
from creator.ingest_runs.models import IngestRun


logger = logging.getLogger(__name__)

# Is there a more extensible way to do this?
GWO_FILE_TYPE = "GWO"


def run_ingest(ingest_run_id=None):
    """
    Run ingest process for a given set of files.
    """
    ingest_run = get_ingest_run(ingest_run_id)
    logging.info(f"Preparing ingest run {ingest_run.pk} for processing.")

    # Check if any IngestRuns with the same input hash already exist
    others = IngestRun.objects.filter(
        state="running",
        input_hash=ingest_run.input_hash
    ).all()

    # Cancel them
    for running_ingest in others:
        logging.info(f"Cancelling previous run '{running_ingest.pk}'")
        django_rq.enqueue(cancel_ingest, running_ingest.pk)

    # Update run state so we know it's running
    ingest_run.start()
    ingest_run.save()

    versions = ingest_run.versions
    if all(
        (
            version.root_file.file_type == GWO_FILE_TYPE
            for version in versions
        )
    ):
        print("All files in the ingest run are genomic workflow manifests.")
        ingest_genomic_workflow_ouput_manifests(versions)

    # Update run state upon completion
    print(f"Finished ingest run {ingest_run_id}")
    ingest_run.complete()
    ingest_run.save()


def cancel_ingest(ingest_run_id):
    # TODO
    print(f"Cancelling ingest run {ingest_run_id}")
    ingest_run = get_ingest_run(ingest_run_id)
    ingest_run.cancel()
    ingest_run.save()


def ingest_genomic_workflow_ouput_manifests(versions):
    # TODO
    print(f"Begin ingesting genomic workflow manifests: {versions}")


def get_ingest_run(ingest_run_id):
    """
    Obtain the IngestRun with id _ingest_run_id_.
    """
    try:
        ingest_run = IngestRun.objects.get(pk=ingest_run_id)
    except Exception as err:
        logging.info(
            f"Getting IngestRun with id={ingest_run_id} failed: {err}"
        )
        raise

    return ingest_run
