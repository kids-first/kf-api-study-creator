from graphql_relay import to_global_id
from creator.studies.factories import StudyFactory
from creator.projects.factories import ProjectFactory
from creator.events.models import Event
from django.contrib.auth import get_user_model

User = get_user_model()

LINK_PROJECT = """
mutation ($study: ID!, $project: ID!) {
    linkProject(study: $study, project: $project) {
        study {
            id
            kfId
            projects { edges { node { id projectId } } }
        }
    }
}
"""

UNLINK_PROJECT = """
mutation ($study: ID!, $project: ID!) {
    unlinkProject(study: $study, project: $project) {
        study {
            id
            kfId
            projects { edges { node { id projectId } } }
        }
        project {
            id
            projectId
            study { id kfId }
        }
    }
}
"""


def test_link_project_event(
    admin_client, db, mocker, settings, mock_cavatica_api
):
    """
    Test that linking a project prouduces an event
    """
    study = StudyFactory(files=0)
    project = ProjectFactory()

    variables = {
        "project": to_global_id("ProjectNode", project.project_id),
        "study": to_global_id("StudyNode", study.kf_id),
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": LINK_PROJECT, "variables": variables},
    )

    assert Event.objects.count() == 1
    assert Event.objects.filter(event_type="PR_LIN").count() == 1

    pr_lin = Event.objects.filter(event_type="PR_LIN").first()
    assert pr_lin.user == User.objects.first()
    assert pr_lin.study == study


def test_unlink_project_event(
    admin_client, db, mocker, settings, mock_cavatica_api
):
    """
    Test that unlinking a project prouduces an event
    """
    study = StudyFactory(files=0)
    project = ProjectFactory(study=study)

    variables = {
        "project": to_global_id("ProjectNode", project.project_id),
        "study": to_global_id("StudyNode", study.kf_id),
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UNLINK_PROJECT, "variables": variables},
    )

    assert Event.objects.count() == 1
    assert Event.objects.filter(event_type="PR_UNL").count() == 1

    pr_unl = Event.objects.filter(event_type="PR_UNL").first()
    assert pr_unl.user == User.objects.first()
    assert pr_unl.study == study
