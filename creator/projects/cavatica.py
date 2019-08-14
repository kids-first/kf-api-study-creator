import pytz
import sevenbridges as sbg
from django.conf import settings
from creator.projects.models import Project, WORKFLOW_TYPES


def create_project(study, project_type, workflow_type=None):
    """
    Create Cavatica project for a given study of a project type
    either 'harmonization' or 'delivery'
    The provided workflow_type will be appended at the end of the project_id
    for the project, and the display value of workflow type name will be
    appended at the end of the name for the project.
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
        created_on=cavatica_project.created_on,
        modified_on=cavatica_project.modified_on,
        study=study,
    )
    project.save()

    return project


def setup_cavatica(study, workflows=None):
    """
    Entry point to set up Cavatica projects for a study
    On creating a new study, the user can give a list of workflow types, and
    one harmonization project would be created for each workflow type.
    If no workflow types are given, harmonization projects would be created
    with default workflow types as specified by CAVATICA_DEFAULT_WORKFLOWS
    """
    if workflows is None:
        workflows = settings.CAVATICA_DEFAULT_WORKFLOWS

    delivery_project = create_project(study, "DEL")
    projects = [delivery_project]
    for workflow in workflows:
        projects.append(create_project(study, "HAR", workflow))

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

    for cavatica_project in api.projects.query().all():
        if project_type == "HAR" and (
            "harmonization" not in cavatica_project.id
            or not any(
                [
                    workflow_choice[1] in cavatica_project.name
                    for workflow_choice in WORKFLOW_TYPES
                ]
            )
        ):
            continue

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
                "project_type": project_type,
                "workflow_type": "bwa-mem",
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

    return created_projects, updated_projects


def sync_cavatica_projects():
    """
    Synchronize projects for all types
    """
    created_har, updated_har = sync_cavatica_account("HAR")
    created_del, updated_del = sync_cavatica_account("DEL")

    return created_har + created_del, updated_har + updated_del
