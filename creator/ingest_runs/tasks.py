import logging
from pprint import pformat

from django.core.exceptions import ValidationError
import pandas

from creator.decorators import task
from creator.analyses.analyzer import extract_data
from creator.files.models import FileType
from creator.ingest_runs.genomic_data_loader import GenomicDataLoader
from creator.ingest_runs.models import IngestRun
from creator.utils import stop_job

logger = logging.getLogger(__name__)


@task("run_ingest")
def run_ingest(ingest_run_uuid=None):
    """
    Run ingest process for a given set of files.
    """
    ingest_run = IngestRun.objects.get(pk=ingest_run_uuid)
    logging.info(f"Preparing ingest run {ingest_run.pk} for processing.")

    # Update run state so we know it's running
    logging.info(f"Start ingest {ingest_run.pk}")
    ingest_run.start()
    ingest_run.save()

    # Check that the files are genomic workflow manifests
    versions = ingest_run.versions.all()
    are_gwo = all(check_gwo(version) for version in versions)
    if are_gwo:
        logging.info(
            "All files in the ingest run are genomic workflow manifests."
        )
        try:
            ingest_genomic_workflow_output_manifests(ingest_run)
        except Exception:
            ingest_run.fail()
            ingest_run.save()
            raise
    else:
        ingest_run.fail()
        ingest_run.save()
        raise Exception("Unknown file type detected in the ingest run.")
    logging.info(f"Ingest run {ingest_run.pk} complete!")
    ingest_run.complete()
    ingest_run.save()


def check_gwo(version):
    return version.root_file.file_type == FileType.GWO.value


@task("cancel_ingest")
def cancel_ingest(ingest_run_uuid=None):
    """
    TODO - docstring
    """
    ingest_run = IngestRun.objects.get(pk=ingest_run_uuid)
    logging.info(f"Canceling ingest run {ingest_run.pk}...")
    ingest_run.cancel()
    ingest_run.save()


def ingest_genomic_workflow_output_manifests(ingest_run):
    """
    TODO docstring
    """
    versions = ingest_run.versions.all()
    logger.info(
        "Begin ingesting genomic workflow manifests: "
        f"{len(versions)}: {pformat(list(versions))}"
    )
    rows = []
    for version in ingest_run.versions.all():
        rows.extend(extract_data(version))
    manifest_df = pandas.DataFrame(rows)

    loader = GenomicDataLoader(version.root_file.study.kf_id)
    df = loader.ingest_gwo(manifest_df)
