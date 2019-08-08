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

    for workflow_choice in WORKFLOW_TYPES:
        if workflow_choice[0] == workflow_type:
            cavatica_project.name = study.name + " " + workflow_choice[1]
            break

    cavatica_project.save()

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
