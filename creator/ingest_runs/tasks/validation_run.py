import django_rq
import logging


from creator.decorators import task
from creator.ingest_runs.models import ValidationRun


logger = logging.getLogger(__name__)


@task("run_validation")
def run_validation(validation_run_uuid=None):
    """
    TODO
    Run validation process for a given set of files.
    """
    validation_run = ValidationRun.objects.get(pk=validation_run_uuid)
    logging.info(
        f"Preparing validation run {validation_run.pk} for processing"
    )


@task("cancel_validation")
def cancel_validation(validation_run_uuid=None):
    """
    TODO
    Cancel validation run
    """
    validation_run = ValidationRun.objects.get(pk=validation_run_uuid)
    logging.info(f"Cancelling validation run {validation_run.pk}")
