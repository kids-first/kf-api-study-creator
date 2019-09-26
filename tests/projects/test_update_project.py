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
    "user_type,authorized,expected",
    [
        ("admin", True, True),
        ("service", True, True),
        ("user", True, False),
        (None, True, False),
    ],
)
def test_update_project_mutation(
    db,
    admin_client,
    service_client,
    user_client,
    client,
    user_type,
    authorized,
    expected,
):
    """
    Only Admins should be allowed to update projects
    """
    project = ProjectFactory(
        project_id="test/my-project", workflow_type="bwa-mem"
    )

    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    project_id = to_global_id("ProjectNode", "test/my-project")
    variables = {"id": project_id, "input": {"workflowType": "rsem"}}
    resp = api_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_PROJECT_MUTATION, "variables": variables},
    )

    if expected:
        resp_body = resp.json()["data"]["updateProject"]["project"]
        assert resp_body["workflowType"] == "rsem"
        assert Project.objects.first().workflow_type == "rsem"
    else:
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")


def test_update_project_event(db, admin_client):
    """
    Test that events are emitted correctly
    """
    project = ProjectFactory(
        project_id="test/my-project", workflow_type="bwa-mem"
    )

    project_id = to_global_id("ProjectNode", "test/my-project")
    variables = {"id": project_id, "input": {"workflowType": "rsem"}}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_PROJECT_MUTATION, "variables": variables},
    )

    assert Event.objects.count() == 1
    event = Event.objects.first()
    assert event.study == project.study
    assert event.project == project
