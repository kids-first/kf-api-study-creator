import sevenbridges as sbg
from django.conf import settings
from creator.projects.models import Project


def create_project(study, project_type):
    """
    Create Cavatica project for a given study of a project type
    either 'harmonization' or 'delivery'
    """
    token = None
    name = study.kf_id
    if project_type == "HAR":
        token = settings.CAVATICA_HARMONIZATION_TOKEN
        name = study.kf_id + "-harmonization"
    elif project_type == "DEL":
        token = settings.CAVATICA_DELIVERY_TOKEN
    else:
        raise "Invalid project type."

    api = sbg.Api(url=settings.CAVATICA_URL, token=token)
    cavatica_project = api.projects.create(name=name)
    cavatica_project.name = study.name
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
        created_by=cavatica_project.created_by,
        created_on=cavatica_project.created_on,
        modified_on=cavatica_project.modified_on,
        study=study,
    )
    project.save()

    return project


def setup_cavatica(study):
    """
    Entry point to set up Cavatica projects for a study
    1. Create a harmonization project
    2. Create a delivery project
    """
    harmonization_project = create_project(study, "HAR")
    delivery_project = create_project(study, "DEL")

    return [harmonization_project, delivery_project]
