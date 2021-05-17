import logging
import pytz
from datetime import datetime
from django.conf import settings
from django_rq import job
from django.contrib.auth import get_user_model

from creator.decorators import task
from creator.buckets.buckets import new_bucket
from creator.studies.dataservice import sync_dataservice_studies
from creator.projects.cavatica import (
    setup_cavatica,
    sync_cavatica_projects,
    import_volume_files,
)
from creator.slack import setup_slack, summary_post
from creator.analyses.analyzer import analyze_version
from creator.buckets.scanner import sync_buckets
from creator.projects.models import Project
from creator.organizations.models import Organization
from creator.studies.models import Study
from creator.files.models import Version
from creator.events.models import Event

User = get_user_model()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@task("setup_bucket")
def setup_bucket_task(kf_id):
    """
    Setup new s3 resources for a study

    :param kf_id: The kf_id of the study to set up the bucket for
    """
    logger.info(f"Creating new buckets for study {kf_id}")

    try:
        study = Study.objects.get(kf_id=kf_id)
    except Study.DoesNotExist:
        logger.error(f"Could not find study {kf_id}")
        raise

    try:
        message = f"Creating buckets for study {kf_id}"
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="BK_STR",
        )
        event.save()

        # Setting up bucket will set the s3 location on the study so it
        # needs to be captured and saved
        study = new_bucket(study)
        study.save()

        message = f"Successfully created buckets for study {kf_id}"
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="BK_SUC",
        )
        event.save()

        logger.info(message)
    except Exception as exc:
        message = (
            f"There was a problem creating buckets for study "
            f"{kf_id}: {exc}"
        )
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="BK_ERR",
        )
        event.save()

        logger.error(message)
        raise


@task("setup_cavatica")
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
        logger.warning(f"Could not find user with sub {user_sub}")
        user = None

    try:
        message = f"Creating Cavatica projects for study {kf_id}"
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="PR_STR",
        )
        event.save()

        setup_cavatica(study, workflows=workflows, user=user)

        message = f"Successfully created Cavatica projects for study {kf_id}"
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="PR_SUC",
        )
        event.save()

        logger.info(message)
    except Exception as exc:
        message = (
            f"There was a problem creating Cavatica projects for study "
            f"{kf_id}: {exc}"
        )
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="PR_ERR",
        )
        event.save()

        logger.error(message)
        raise


@task("import_delivery_files")
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
        logger.warning(f"Could not find user with sub {user_sub}")
        user = None

    try:
        message = f"Importing volume files to Cavatica project {project_id}"
        event = Event(
            organization=Organization.objects.earliest("created_on"),
            study=study,
            description=message,
            user=user,
            event_type="IM_STR",
        )
        event.save()

        folder_name = import_volume_files(project)

        message = (
            f"Successfully imported volume files to "
            f"Cavatica project {project_id} under the {folder_name} folder"
        )
        event = Event(
            organization=Organization.objects.earliest("created_on"),
            study=study,
            description=message,
            event_type="IM_SUC",
        )
        event.save()

        logger.info(message)
    except Exception as exc:
        message = (
            f"There was a problem importing volume files to the Cavatica "
            f"project {project_id}: {exc}"
        )
        event = Event(
            organization=Organization.objects.earliest("created_on"),
            study=study,
            description=message,
            event_type="IM_ERR",
        )
        event.save()

        logger.error(message)
        raise


@task(job="cavatica_sync")
def sync_cavatica_projects_task():
    """
    Synchronize Cavatica projects with the Study Creator
    """
    sync_cavatica_projects()


@task(job="dataservice_sync")
def sync_dataservice_studies_task():
    """
    Synchronize Dataservice studies with the Study Creator
    """
    sync_dataservice_studies()


@task(job="buckets_sync")
def sync_buckets_task():
    """
    Synchronize buckets in S3
    """
    sync_buckets()


@task(job="setup_slack")
def setup_slack_task(kf_id):
    """
    Setup a Slack channel for the new study
    """
    try:
        study = Study.objects.get(kf_id=kf_id)
    except Study.DoesNotExist:
        logger.error(f"Could not find study {kf_id}")
        raise

    message = f"Creating a Slack channel for study {kf_id}"
    logger.info(message)
    event = Event(
        organization=study.organization,
        study=study,
        description=message,
        event_type="SL_STR",
    )
    event.save()

    try:
        setup_slack(study)
    except Exception as exc:
        message = (
            f"There was a problem creating a Slack channel for study "
            f"{kf_id}: {exc}"
        )
        event = Event(
            organization=study.organization,
            study=study,
            description=message,
            event_type="SL_ERR",
        )
        event.save()

        logger.error(message)
        return

    message = f"Successfully created Slack channel for study {kf_id}"
    logger.info(message)
    event = Event(
        organization=study.organization,
        study=study,
        description=message,
        event_type="SL_SUC",
    )
    event.save()


@task(job="slack_notify")
def slack_notify_task():
    """
    Runs the daily Slack study updates job
    """
    summary_post()


@task(job="analyzer")
def analyzer_task():
    """
    Analyze any un-analyzed versions
    """
    versions = (
        Version.objects.filter(analysis=None)
        | Version.objects.filter(analysis__known_format=False)
    ).all()
    logger.info(f"Found {len(versions)} versions to analyze")
    errors = 0
    for version in versions.all():
        try:
            analysis = analyze_version(version)
        except Exception:
            errors += 1
            logger.warning(f"Failed to analyze version {version.kf_id}")
            continue
        analysis.user = version.creator
        analysis.save()
    logger.info(
        f"Successfully analyzed {len(versions) - errors} versions. "
        f"Failed to analyze {errors} versions."
    )
