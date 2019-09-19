import pytest
import pytz
import sevenbridges as sbg
from graphql_relay import to_global_id
from unittest.mock import MagicMock
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from creator.projects.cavatica import (
    setup_cavatica,
    create_project,
    copy_users,
)
from creator.studies.models import Study
from creator.projects.models import Project


CREATE_PROJECT_MUTATION = """
mutation newProject($input: ProjectInput!) {
    createProject(input: $input) {
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


@pytest.fixture(autouse=True)
def enable_projects(settings):
    settings.FEAT_CAVATICA_CREATE_PROJECTS = True
    settings.CAVATICA_HARMONIZATION_TOKEN = "abc"


@pytest.mark.parametrize(
    "user_type,authorized,expected",
    [
        ("admin", True, True),
        ("service", True, True),
        ("user", True, False),
        (None, True, False),
    ],
)
def test_create_project_mutation(
    db,
    admin_client,
    service_client,
    user_client,
    client,
    mock_cavatica_api,
    user_type,
    authorized,
    expected,
):
    """
    Only Admins should be allowed to create new projects
    """
    study = Study(kf_id="SD_00000000")
    study.save()

    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    kf_id = to_global_id("StudyNode", "SD_00000000")
    variables = {"input": {"workflowType": "rsem", "study": kf_id}}
    resp = api_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_PROJECT_MUTATION, "variables": variables},
    )

    if expected:
        resp_body = resp.json()["data"]["createProject"]["project"]
        assert resp_body["workflowType"] == "rsem"
        assert Project.objects.count() == 1
        assert Project.objects.first().workflow_type == "rsem"
    else:
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")
        assert Project.objects.count() == 0


def test_create_project_study_does_not_exist(db, admin_client):
    """
    Test that a project may not be created when a study is not valid
    """
    kf_id = to_global_id("StudyNode", "SD_00000000")
    variables = {"input": {"workflowType": "rsem", "study": kf_id}}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_PROJECT_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"].startswith("Study does not")
    assert Project.objects.count() == 0


def test_create_project_no_duplicate_workflows(
    db, admin_client, mock_cavatica_api
):
    """
    Test that multiple projects with the same workflow may not be created for
    the same study.
    """
    study = Study(kf_id="SD_00000000")
    study.save()

    kf_id = to_global_id("StudyNode", "SD_00000000")
    variables = {"input": {"workflowType": "rsem", "study": kf_id}}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_PROJECT_MUTATION, "variables": variables},
    )

    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_PROJECT_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"].startswith("Study already has")
    assert Project.objects.count() == 1
