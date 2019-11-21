import logging
from django_rq import job
from django.contrib.auth import get_user_model

from creator.studies.bucketservice import setup_bucket
from creator.projects.cavatica import setup_cavatica
from creator.studies.models import Study
from creator.events.models import Event

User = get_user_model()

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


@job
def setup_cavatica_task(kf_id, workflows, user_sub):
    """
    Setup new Cavatica projects for a new study

    :param kf_id: The kf_id of the study to set up projects for
    :param workflows: The types of workflows to setup projects for
    :param user_sub: The sub of the user which initiated the project creation
    """
    logger.info(f"Creating projects in Cavatica for {kf_id}")

    try:
        study = Study.objects.get(kf_id=kf_id)
    except Study.DoesNotExist:
        logger.error(f"Could not find study {kf_id}")

    try:
        user = User.objects.get(sub=user_sub)
    except User.DoesNotExist:
        logger.warn(f"Could not find user with sub {user_sub}")
        user = None

    try:
        message = f"Creating Cavatica projects for study {kf_id}"
        event = Event(study=study, description=message, event_type="PR_STR")
        event.save()

        setup_cavatica(study, workflows=workflows, user=user)

        message = f"Successfully created Cavatica projects for study {kf_id}"
        event = Event(study=study, description=message, event_type="PR_SUC")
        event.save()

        logger.info(message)
    except Exception as exc:
        message = (
            f"There was a problem creating Cavatica projects for study "
            f"{kf_id}: {exc}"
        )
        event = Event(study=study, description=message, event_type="PR_ERR")
        event.save()

        logger.error(message)
        return
