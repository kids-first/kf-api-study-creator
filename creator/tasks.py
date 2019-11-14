import logging
from django_rq import job
from creator.studies.bucketservice import setup_bucket
from creator.studies.models import Study
from creator.events.models import Event

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@job
def setup_bucket_task(kf_id):
    """
    Setup new s3 resources for a study by calling the bucket service

    :param kf_id: The kf_id of the study to set up the bucket for
    """
    logger.info(f"Creating a new bucket with Bucket Service for {kf_id}")

    try:
        study = Study.objects.get(kf_id=kf_id)
    except Study.DoesNotExist:
        logger.error(f"Could not find study {kf_id}")

    try:
        message = f"Creating a bucket for study {kf_id}"
        event = Event(study=study, description=message, event_type="BK_STR")
        event.save()

        # Setting up bucket will set the s3 location on the study so it
        # needs to be captured and saved
        study = setup_bucket(study)
        study.save()

        message = f"Successfully created bucket for study {kf_id}"
        event = Event(study=study, description=message, event_type="BK_SUC")
        event.save()

        logger.info(message)
    except Exception as exc:
        message = (
            f"There was a problem calling the bucket service for study "
            f"{kf_id}: {exc}"
        )
        event = Event(study=study, description=message, event_type="BK_ERR")
        event.save()

        logger.error(message)
        return
