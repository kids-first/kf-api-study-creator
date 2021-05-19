import logging
from pprint import pformat

from django.conf import settings
import pandas

from creator.decorators import task
from creator.analyses.analyzer import extract_data
from creator.files.models import FileType
from creator.ingest_runs.genomic_data_loader import GenomicDataLoader
from creator.ingest_runs.models import IngestRun

logger = logging.getLogger(__name__)


@task("run_ingest")
def run_ingest(ingest_run_uuid=None):
    """
    Run ingest process for a given set of files.
    """
    ingest_run = IngestRun.objects.get(pk=ingest_run_uuid)
    logger.info(f"Preparing ingest run {ingest_run.pk} for processing.")

    # Update run state so we know it's running
    logger.info(f"Start ingest {ingest_run.pk}")
    ingest_run.start()
    ingest_run.save()

    # Check that the files are genomic workflow manifests
    versions = ingest_run.versions.all()
    are_gwo = all(check_gwo(version) for version in versions)
    try:
        if are_gwo:
            # If FEAT_INGEST_GENOMIC_WORKFLOW_OUTPUTS is enabled, try to run
            # the custom ingest process for genomic workflow manifests. If it's
            # not enabled, raise an error and nothing else happens.
            if not settings.FEAT_INGEST_GENOMIC_WORKFLOW_OUTPUTS:
                raise Exception(
                    "Ingesting genomic workflow output manifests is not "
                    "enabled. Make sure that the "
                    "FEAT_INGEST_GENOMIC_WORKFLOW_OUTPUTS is set."
                )
            else:
                logger.info(
                    "All files in the ingest run are genomic workflow "
                    "manifests."
                )
                ingest_genomic_workflow_output_manifests(ingest_run)
        else:
            raise Exception("Unknown file type detected in the ingest run.")
    except Exception as e:
        ingest_run.fail(error_msg=str(e))
        ingest_run.save()
        raise

    logger.info(f"Ingest run {ingest_run.pk} complete!")
    ingest_run.complete()
    ingest_run.save()


def check_gwo(version):
    return version.root_file.file_type == FileType.GWO.value


@task("cancel_ingest")
def cancel_ingest(ingest_run_uuid=None):
    """
    Cancel an ingest process for a given _ingest_run_uuid_.
    """
    ingest_run = IngestRun.objects.get(pk=ingest_run_uuid)
    logger.info(f"Canceling ingest run {ingest_run.pk}...")
    ingest_run.cancel()
    ingest_run.save()


def ingest_genomic_workflow_output_manifests(ingest_run):
    """
    Perform the full ingest process for genomic workflow output manifests.
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

    loader = GenomicDataLoader(version.root_file.study, ingest_run)
    loader.ingest_gwo(manifest_df)
