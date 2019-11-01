import logging
import pytz
import sevenbridges as sbg
from django.conf import settings
from creator.projects.models import Project, WORKFLOW_TYPES
from creator.events.models import Event

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_project(study, project_type, workflow_type=None, user=None):
    """
    Create Cavatica project for a given study of a project type
    either 'harmonization' or 'delivery'
    The provided workflow_type will be appended at the end of the project_id
    for the project, and the display value of workflow type name will be
    appended at the end of the name for the project.
    If volume mounting is enabled, the study's bucket will be attached to the
    new project.
    """
    token = None
    name = study.kf_id
    if project_type == "HAR":
        token = settings.CAVATICA_HARMONIZATION_TOKEN
        name = study.kf_id + "-" + workflow_type
    elif project_type == "DEL":
        token = settings.CAVATICA_DELIVERY_TOKEN
    else:
        raise "Invalid project type."

    api = sbg.Api(url=settings.CAVATICA_URL, token=token)
    cavatica_project = api.projects.create(name=name)
    cavatica_project.name = study.name if study.name else study.kf_id

    for workflow_choice in WORKFLOW_TYPES:
        if workflow_choice[0] == workflow_type:
            cavatica_project.name = (
                cavatica_project.name + " " + workflow_choice[1]
            )
            break
    try:
        cavatica_project.save()
    except sbg.errors.ResourceNotModified:
        pass

    description = (
        cavatica_project.description if cavatica_project.description else ""
    )
    project = Project(
        project_id=cavatica_project.id,
        name=cavatica_project.name,
        description=description,
        url=cavatica_project.href,
        project_type=project_type,
        workflow_type=workflow_type,
        created_by=cavatica_project.created_by,
        created_on=cavatica_project.created_on.replace(tzinfo=pytz.UTC),
        modified_on=cavatica_project.modified_on.replace(tzinfo=pytz.UTC),
        study=study,
    )
    project.save()

    # Log an event
    if user:
        message = f"{user.username} created project {cavatica_project.id}"
    else:
        message = f"A new project was created {cavatica_project.id}"
    event = Event(
        study=study, project=project, description=message, event_type="PR_CRE"
    )
    # Only add the user if they are in the database (not a service user)
    if user and not user._state.adding:
        event.user = user
    event.save()

    # Only copy users for analysis projects
    if project_type == "HAR":
        copy_users(api, cavatica_project)

    # Attach S3 volume, no-op if the correct settings are not set
    return project


def copy_users(api, project):
    """
    Copy users from a given template project onto a different project.
    Users will be copied using the CAVATICA_HARMONIZATION_TOKEN account and
    so whatever account is associated with that token will need to have access
    to the template project, as defined by the CAVATICA_USER_ACCESS_PROJECT.
    """
    if (
        not settings.FEAT_CAVATICA_COPY_USERS
        or not settings.CAVATICA_USER_ACCESS_PROJECT
    ):
        return

    user_project = api.projects.get(id=settings.CAVATICA_USER_ACCESS_PROJECT)
    # Couldn't find project
    if user_project.id is None:
        return

    users = list(user_project.get_members())
    for user in users:
        try:
            project.add_member(user.username, permissions=user.permissions)
        except sbg.errors.Conflict:
            # We may have tried to add ourselves back to the project that
            # we already own, so ignore that error.
            pass


def attach_volume(study):
    """
    Attaches a study bucket to the Harmonization's Cavatica account.
    Will use the CAVATICA_READWRITE_* keys to create the volume in the
    CAVATICA_HARMONIZATION_ACCOUNT and will add the CAVATICA_DELIVERY_ACCOUNT
    as a member of the volume with read and copy permissions.
    """
    # Check that mounting volumes is enabled
    if not settings.FEAT_CAVATICA_MOUNT_VOLUMES:
        return

    api = sbg.Api(
        url=settings.CAVATICA_URL, token=settings.CAVATICA_HARMONIZATION_TOKEN
    )

    access_key = settings.CAVATICA_READWRITE_ACCESS_KEY
    secret_key = settings.CAVATICA_READWRITE_SECRET_KEY
    access_mode = "RW"

    # Make sure that the keys were set correctly
    if access_key is None or secret_key is None:
        raise "Volume mounting is enabled but keys are not set correctly"

    # Now we know that all settings are in place to attach a volume

    new_volume = api.volumes.create_s3_volume(
        name=study.kf_id,
        description=f"Created by the Study Creator for '{study.name}'",
        bucket=study.bucket,
        access_key_id=access_key,
        secret_access_key=secret_key,
        access_mode=access_mode,
    )

    logger.info(
        f"Adding {settings.CAVATICA_DELIVERY_ACCOUNT} "
        "as a member to the volume"
    )

    try:
        member = new_volume.add_member(
            settings.CAVATICA_DELIVERY_ACCOUNT,
            permissions={
                "write": False,
                "read": True,
                "copy": True,
                "admin": False,
            },
        )
    except sbg.errors.Conflict as err:
        logger.warn(
            f"Unable to add {settings.CAVATICA_DELIVERY_ACCOUNT} to the "
            f"volume. Perhaps they are already a member? {err}"
        )

    return new_volume


def setup_cavatica(study, workflows=None, user=None):
    """
    Entry point to set up Cavatica projects for a study
    On creating a new study, the user can give a list of workflow types, and
    one harmonization project would be created for each workflow type.
    If no workflow types are given, harmonization projects would be created
    with default workflow types as specified by CAVATICA_DEFAULT_WORKFLOWS
    """
    if workflows is None:
        workflows = settings.CAVATICA_DEFAULT_WORKFLOWS

    delivery_project = create_project(study, "DEL", user=user)
    projects = [delivery_project]
    for workflow in workflows:
        projects.append(create_project(study, "HAR", workflow, user=user))

    if (
        settings.FEAT_CAVATICA_MOUNT_VOLUMES
        and settings.CAVATICA_URL
        and settings.CAVATICA_HARMONIZATION_TOKEN
        and settings.CAVATICA_READWRITE_ACCESS_KEY
        and settings.CAVATICA_READWRITE_SECRET_KEY
        and settings.CAVATICA_DELIVERY_ACCOUNT
    ):
        attach_volume(study)

    return projects


def sync_cavatica_account(project_type):
    """
    Look at all projects for given project type and update or create projects
    as needed and return changes
    """
    token = None
    if project_type == "HAR":
        token = settings.CAVATICA_HARMONIZATION_TOKEN
    elif project_type == "DEL":
        token = settings.CAVATICA_DELIVERY_TOKEN
    else:
        raise "Invalid project type."

    api = sbg.Api(url=settings.CAVATICA_URL, token=token)

    created_projects = []
    updated_projects = []
    # Keep track of all the projects Cavatica side so we can compare internally
    # later to determine if anything was deleted
    seen_projects = set()
    db_projects = {
        project["project_id"]
        for project in Project.objects.filter(
            project_type=project_type, deleted=False
        )
        .values("project_id")
        .all()
    }

    for cavatica_project in api.projects.query().all():
        seen_projects.add(cavatica_project.id)

        description = (
            cavatica_project.description
            if cavatica_project.description
            else ""
        )

        try:
            project = Project.objects.get(project_id=cavatica_project.id)
            modified_on = project.modified_on
        except Project.DoesNotExist:
            project = None
            modified_on = None

        project, created = Project.objects.update_or_create(
            project_id=cavatica_project.id,
            defaults={
                "name": cavatica_project.name,
                "description": description,
                "url": cavatica_project.href,
                "workflow_type": "bwa_mem",
                "created_by": cavatica_project.created_by,
                "created_on": cavatica_project.created_on.replace(
                    tzinfo=pytz.UTC
                ),
                "modified_on": cavatica_project.modified_on.replace(
                    tzinfo=pytz.UTC
                ),
            },
        )

        if created:
            created_projects.append(project)
        elif modified_on and modified_on < project.modified_on:
            updated_projects.append(project)

    # If there are projects in the database that weren't seen in Cavatica,
    # mark them as deleted
    deleted_projects = db_projects - seen_projects
    for project in deleted_projects:
        Project.objects.filter(project_id=project).update(deleted=True)
    deleted_projects = list(
        Project.objects.in_bulk(list(deleted_projects)).values()
    )

    # Save everything
    for project in created_projects + updated_projects + deleted_projects:
        project.save()

    # Emit events
    for project in created_projects:
        message = (
            f"New project was discovered in Cavatica: {cavatica_project.id}"
        )
        event = Event(
            project=project, description=message, event_type="PR_CRE"
        )
        event.save()

    for project in updated_projects:
        message = f"Project was updated in Cavatica: {cavatica_project.id}"
        event = Event(
            project=project, description=message, event_type="PR_UPD"
        )
        event.save()

    for project in deleted_projects:
        message = f"Project was deleted in Cavatica: {cavatica_project.id}"
        event = Event(
            project=project, description=message, event_type="PR_DEL"
        )
        event.save()

    return created_projects, updated_projects, deleted_projects


def sync_cavatica_projects():
    """
    Synchronize projects for all types
    """
    created_har, updated_har, deleted_har = sync_cavatica_account("HAR")
    created_del, updated_del, deleted_del = sync_cavatica_account("DEL")

    return (
        created_har + created_del,
        updated_har + updated_del,
        deleted_har + deleted_del,
    )
