import pytest
from graphql_relay import to_global_id
from creator.projects.models import Project
from creator.projects.factories import ProjectFactory
from creator.events.models import Event


UPDATE_PROJECT_MUTATION = """
mutation updateProject($id: ID!, $input: UpdateProjectInput!) {
    updateProject(id: $id, input: $input) {
        project {
            projectId
            name
            description
            createdOn
            modifiedOn
            workflowType
        }
    }
}
"""


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", False),
        ("Investigators", False),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_update_project_mutation(db, clients, user_group, allowed):
    """
    Test that correct users are able to update projects
    """
    client = clients.get(user_group)

    project = ProjectFactory(
        project_id="test/my-project", workflow_type="bwa-mem"
    )

    project_id = to_global_id("ProjectNode", "test/my-project")
    variables = {"id": project_id, "input": {"workflowType": "rsem"}}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_PROJECT_MUTATION, "variables": variables},
    )

    if allowed:
        resp_body = resp.json()["data"]["updateProject"]["project"]
        assert resp_body["workflowType"] == "rsem"
        assert Project.objects.first().workflow_type == "rsem"
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_update_project_event(db, clients):
    """
    Test that events are emitted correctly
    """
    client = clients.get("Administrators")

    project = ProjectFactory(
        project_id="test/my-project", workflow_type="bwa-mem"
    )

    project_id = to_global_id("ProjectNode", "test/my-project")
    variables = {"id": project_id, "input": {"workflowType": "rsem"}}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_PROJECT_MUTATION, "variables": variables},
    )

    assert Event.objects.count() == 1
    event = Event.objects.first()
    assert event.study == project.study
    assert event.project == project
