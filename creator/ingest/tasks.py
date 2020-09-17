import logging
from django_rq import job

from creator.ingest.models import Validation


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@job
def run_validation(validation_id):
    """
    Run ingest validation.

    :param validation_id: The primary identifier of the Validation to run.
    """
    logger.info(f"Running computation for Validation {validation_id}")

    try:
        validation = Validation.objects.get(id=validation_id)
    except Validation.DoesNotExist:
        logger.error(f"Could not find validation {validation_id}")
        raise

    try:
        logger.info("Run validation now!")
        # We will just add something to the result field for now
        validation.result = {"status": "complete"}
        validation.save()
    except Exception as exc:
        logger.error(f"There was an error running validation! {exc}")
        raise
