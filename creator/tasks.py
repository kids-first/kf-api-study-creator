import logging
import pytz
from datetime import datetime
from django_rq import job
from django.contrib.auth import get_user_model

from creator.studies.bucketservice import setup_bucket
from creator.studies.dataservice import sync_dataservice_studies
from creator.projects.cavatica import (
    setup_cavatica,
    sync_cavatica_projects,
    import_volume_files,
)
from creator.projects.models import Project
from creator.studies.models import Study
from creator.events.models import Event
from creator.models import Job

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
        raise

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
        raise

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


@job
def import_delivery_files_task(project_id, user_sub):
    """
    Import all files from a volume for a given study into a project.

    The name of the volume will be assumed to be that of the kf_id,
    if it is not, the task will fail out.

    :param project_id: The project to import files to
    """
    logger.info(f"Importing volume files to Cavatica for project {project_id}")

    try:
        project = Project.objects.get(project_id=project_id)
    except Project.DoesNotExist:
        logger.error(f"Could not find project {project_id}")
        raise

    study = project.study

    try:
        user = User.objects.get(sub=user_sub)
    except User.DoesNotExist:
        logger.warn(f"Could not find user with sub {user_sub}")
        user = None

    try:
        message = f"Importing volume files to Cavatica project {project_id}"
        event = Event(
            study=study, description=message, user=user, event_type="IM_STR"
        )
        event.save()

        folder_name = import_volume_files(project)

        message = (
            f"Successfully imported volume files to "
            f"Cavatica project {project_id} under the {folder_name} folder"
        )
        event = Event(study=study, description=message, event_type="IM_SUC")
        event.save()

        logger.info(message)
    except Exception as exc:
        message = (
            f"There was a problem importing volume files to the Cavatica "
            f"project {project_id}: {exc}"
        )
        event = Event(study=study, description=message, event_type="IM_ERR")
        event.save()

        logger.error(message)
        return


def sync_cavatica_projects_task():
    """
    Synchronize Cavatica projects with the Study Creator
    """
    job = Job.objects.get(name="cavatica_sync")

    if not job.active:
        logger.info("The cavatica_sync job is not active, will not run")
        return
    logger.info("Running the cavatica_sync job")

    try:
        sync_cavatica_projects()
    except Exception as err:
        job.failing = True
        job.last_error = str(err)
    else:
        job.failing = False
        job.last_error = ""

    job.last_run = datetime.utcnow()
    job.last_run = job.last_run.replace(tzinfo=pytz.UTC)
    job.save()


def sync_dataservice_studies_task():
    """
    Synchronize Dataservice studies with the Study Creator
    """
    job = Job.objects.get(name="dataservice_sync")

    if not job.active:
        logger.info("The dataserivce_sync job is not active, will not run")
        return
    logger.info("Running the dataservice_sync job")

    try:
        sync_dataservice_studies()
    except Exception as err:
        job.failing = True
        job.last_error = str(err)
    else:
        job.failing = False
        job.last_error = ""

    job.last_run = datetime.utcnow()
    job.last_run = job.last_run.replace(tzinfo=pytz.UTC)
    job.save()